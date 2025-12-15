import json
import boto3
import os
from datetime import datetime

# --- 1. CONFIGURATION ---
S3_BUCKET = "marketplace-dev-documents-grp3"
DYNAMODB_TABLE_NAME = "marketplace-dev-bookings-table"
PROVIDER_TABLE_NAME = "marketplace-dev-providers-table"
VERIFIED_SENDER_EMAIL = "taofeekadeyemi22@gmail.com"
SENDER_DISPLAY_NAME = "HOME SERVICES MARKETPLACE <taofeekadeyemi22@gmail.com>"
CLOUDFRONT_URL = "https://d3r7plath9y10q.cloudfront.net"

# --- 2. CLIENT INITIALIZATION ---
try:
    s3 = boto3.client('s3')
    dynamodb_resource = boto3.resource('dynamodb')
    bookings_table = dynamodb_resource.Table(DYNAMODB_TABLE_NAME)
    provider_table = dynamodb_resource.Table(PROVIDER_TABLE_NAME)
    ses_client = boto3.client('ses')
except Exception as e:
    print(f"FATAL: Client init failed: {e}")

# --- 3. HELPER FUNCTIONS ---

def unmarshal_dynamodb_json(node):
    """Converts DynamoDB Stream JSON format (S:{}, N:{}) into a standard Python dictionary."""
    data = {}
    for key, value in node.items():
        if 'S' in value: data[key] = value['S']
        elif 'N' in value: data[key] = value['N']
        elif 'BOOL' in value: data[key] = value['BOOL']
        elif 'M' in value: data[key] = unmarshal_dynamodb_json(value['M'])
    return data

def generate_receipt_html(booking_id, booking_data):
    """Generates the HTML receipt content."""
    try:
        price = float(booking_data.get('servicePrice', 0))
    except:
        price = 0.00

    return f"""
    <html>
    <body>
        <h1>Receipt: {booking_id}</h1>
        <p><strong>Status:</strong> PAID</p>
        <p><strong>Date:</strong> {datetime.now().strftime('%Y-%m-%d')}</p>
        <hr/>
        <p><strong>Service:</strong> {booking_data.get('serviceName', 'Service')}</p>
        <p><strong>Customer:</strong> {booking_data.get('customerName', 'Customer')}</p>
        <p><strong>Address:</strong> {booking_data.get('customerAddress', 'N/A')}</p>
        <h2>Total: CAD ${price:.2f}</h2>
    </body>
    </html>
    """

def lambda_handler(event, context):
    print("🔍 FULL RAW EVENT:", json.dumps(event))

    for record in event['Records']:
        
        # ====================================================
        # ROUTE 1: DYNAMODB STREAM (New Booking -> Confirmation Emails)
        # ====================================================
        if 'dynamodb' in record:
            if record['eventName'] == 'INSERT':
                print("✅ Route 1: Processing DynamoDB Stream (New Booking)")
                try:
                    new_image = record['dynamodb']['NewImage']
                    booking_data = unmarshal_dynamodb_json(new_image)
                    
                    cust_email = booking_data.get('customerEmail')
                    prov_id = booking_data.get('providerId')
                    
                    if not cust_email or not prov_id:
                        continue

                    p_resp = provider_table.get_item(Key={'providerId': prov_id})
                    p_item = p_resp.get('Item', {})
                    p_email = p_item.get('email')

                    if p_email:
                        ses_client.send_email(
                            Source=SENDER_DISPLAY_NAME,
                            Destination={'ToAddresses': [p_email]},
                            Message={
                                'Subject': {'Data': f"New Booking: {booking_data.get('serviceName')}"},
                                'Body': {'Html': {'Data': f"<h2>New Booking!</h2><p>Please log in to confirm.</p>"}}
                            }
                        )
                        print(f"📧 Sent Provider Email to {p_email}")

                    ses_client.send_email(
                        Source=SENDER_DISPLAY_NAME,
                        Destination={'ToAddresses': [cust_email]},
                        Message={
                            'Subject': {'Data': "Booking Confirmation"},
                            'Body': {'Html': {'Data': f"""
                                <h1>Booking Received</h1>
                                <p>Customer ID: {booking_data.get('customerId')}</p>
                                <p>Booking ID: {booking_data.get('bookingId')}</p>
                                <p>Status: PENDING CONFIRMATION</p>
                            """}}
                        }
                    )
                    print(f"📧 Sent Customer Email to {cust_email}")

                except Exception as e:
                    print(f"❌ Error in Route 1 (Emails): {e}")
            continue 

        # ====================================================
        # ROUTE 2: SNS TOPIC (Status Updates)
        # ====================================================
        elif 'Sns' in record:
            print("✅ Route 2: Detected SNS Record (Status Update)")
            
            try:
                sns_message = record['Sns']['Message']
                print(f"📨 SNS Message: {sns_message}")
                
                # Normalize message for checking
                msg_upper = sns_message.upper()

                # --- EXTRACT BOOKING ID ---
                try:
                    words = sns_message.split()
                    booking_id = None
                    if "Booking" in words:
                        id_idx = words.index("Booking") + 1
                        if id_idx < len(words):
                            booking_id = words[id_idx]
                    
                    if not booking_id:
                        for w in words:
                            if w.startswith("booking-"):
                                booking_id = w
                                break
                    
                    if booking_id:
                        booking_id = booking_id.strip(".,")
                        print(f"🆔 Extracted Booking ID: {booking_id}")
                    else:
                        raise ValueError("No ID found")
                except Exception as e:
                    print(f"❌ Error parsing ID: {e}")
                    continue

                # --- FETCH DATA ---
                resp = bookings_table.get_item(Key={'bookingId': booking_id})
                item = resp.get('Item')
                if not item:
                    print(f"❌ Booking {booking_id} not found in DynamoDB")
                    continue
                
                cust_email = item.get('customerEmail')
                cust_id = item.get('customerId')
                provider_name = item.get('providerName', 'The Provider')

                # ====================================================
                # A. STATUS = COMPLETED (Trigger Review Email)
                # ====================================================
                if "NEW STATUS: COMPLETED" in msg_upper:
                    print("✅ Status is COMPLETED. Sending Review Request...")
                    
                    if cust_email and cust_id:
                        review_link = f"{CLOUDFRONT_URL}?customerId={cust_id}"
                        
                        ses_client.send_email(
                            Source=SENDER_DISPLAY_NAME,
                            Destination={'ToAddresses': [cust_email]},
                            Message={
                                'Subject': {'Data': f"How was your service from {provider_name}?"},
                                'Body': {'Html': {'Data': f"""
                                    <h2>Service Completed</h2>
                                    <p>Hi {item.get('customerName', 'Customer')},</p>
                                    <p>Your service with <strong>{provider_name}</strong> has been marked as completed.</p>
                                    <p>We would love to hear about your experience!</p>
                                    
                                    <p style="margin: 20px 0;">
                                        <a href="{review_link}" 
                                           style="background-color: #ff9900; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; font-weight: bold;">
                                            ⭐ Rate & Review Service
                                        </a>
                                    </p>
                                    
                                    <p><small>Or copy this link: {review_link}</small></p>
                                    <p><strong>Your Customer ID:</strong> {cust_id}</p>
                                """}}
                            }
                        )
                        print(f"📧 Review Email sent to {cust_email}")

                # ====================================================
                # B. STATUS = PAID (Trigger Invoice Generation)
                # ====================================================
                elif "NEW STATUS: PAID" in msg_upper:
                    print("💰 Status is PAID. Generating Invoice...")

                    # 1. Generate & Upload Invoice
                    html_body = generate_receipt_html(booking_id, item)
                    file_name = f"invoices/{booking_id}_{datetime.now().strftime('%Y%m%d')}.html"

                    s3.put_object(
                        Bucket=S3_BUCKET,
                        Key=file_name,
                        Body=html_body,
                        ContentType='text/html'
                    )
                    print(f"🚀 Uploaded Invoice to s3://{S3_BUCKET}/{file_name}")

                    # 2. Generate Link & Email Customer
                    if cust_email:
                        presigned_url = s3.generate_presigned_url(
                            'get_object',
                            Params={'Bucket': S3_BUCKET, 'Key': file_name},
                            ExpiresIn=259200 # 3 Days
                        )
                        
                        ses_client.send_email(
                            Source=SENDER_DISPLAY_NAME,
                            Destination={'ToAddresses': [cust_email]},
                            Message={
                                'Subject': {'Data': f"Receipt for Booking {booking_id}"},
                                'Body': {'Html': {'Data': f"""
                                    <h2>Payment Received</h2>
                                    <p>Thank you! Your payment has been processed.</p>
                                    <p><a href="{presigned_url}" style="background:#28a745;color:white;padding:10px 20px;text-decoration:none;border-radius:5px;">Download Official Receipt</a></p>
                                    <p><small>Link expires in 3 days.</small></p>
                                """}}
                            }
                        )
                        print(f"📧 Receipt Link sent to {cust_email}")

                # ====================================================
                # C. STANDARD UPDATES (Confirmed, Cancelled, In Progress)
                # ====================================================
                elif any(status in msg_upper for status in ["CONFIRMED", "CANCELLED", "IN_PROGRESS"]):
                    
                    # Detect which status it is for the display text
                    new_status_display = "UPDATED"
                    if "CONFIRMED" in msg_upper: new_status_display = "CONFIRMED"
                    elif "CANCELLED" in msg_upper: new_status_display = "CANCELLED"
                    elif "IN_PROGRESS" in msg_upper: new_status_display = "IN PROGRESS"

                    print(f"ℹ️ Standard Status Update detected: {new_status_display}")

                    if cust_email:
                        # Define color based on status
                        status_color = "#007bff" # Blue default
                        if "CANCELLED" in msg_upper: status_color = "#dc3545" # Red
                        elif "CONFIRMED" in msg_upper: status_color = "#28a745" # Green

                        ses_client.send_email(
                            Source=SENDER_DISPLAY_NAME,
                            Destination={'ToAddresses': [cust_email]},
                            Message={
                                'Subject': {'Data': f"Booking Update: {new_status_display}"},
                                'Body': {'Html': {'Data': f"""
                                    <html>
                                    <body style="font-family: Arial, sans-serif;">
                                        <h2 style="color: #333;">Booking Status Update</h2>
                                        <p>Hello {item.get('customerName', 'Customer')},</p>
                                        <p>The status of your booking (ID: <b>{booking_id}</b>) has been updated.</p>
                                        <p style="font-size: 18px;">New Status: <strong style="color: {status_color};">{new_status_display}</strong></p>
                                        <br>
                                        <p>Thank you for using Home Services Marketplace.</p>
                                    </body>
                                    </html>
                                """}}
                            }
                        )
                        print(f"📧 Standard Update Email sent to {cust_email}")

                else:
                    print("ℹ️ SNS message received, but status does not trigger an email action.")

            except Exception as e:
                print(f"❌ CRITICAL ERROR in SNS Block: {e}")
                continue

        else:
            print(f"⚠️ Unknown Record Type: {record.keys()}")

    return "Done"
