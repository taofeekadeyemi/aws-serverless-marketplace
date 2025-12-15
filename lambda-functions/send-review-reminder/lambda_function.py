import json
import boto3
import os
from datetime import datetime, timedelta
from boto3.dynamodb.conditions import Attr

# --- CONFIGURATION ---
BOOKINGS_TABLE_NAME = "marketplace-dev-bookings-table"
VERIFIED_SENDER_EMAIL = "taofeekadeyemi22@gmail.com"
SENDER_DISPLAY_NAME = "HOME SERVICES MARKETPLACE <taofeekadeyemi22@gmail.com>"
CLOUDFRONT_URL = "https://d3r7plath9y10q.cloudfront.net"

# --- CLIENTS ---
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(BOOKINGS_TABLE_NAME)
ses_client = boto3.client('ses')

def lambda_handler(event, context):
    print("⏰ Starting Daily Review Reminder Job...")
    
    try:      
        # ROBUST VERSION: Checks for 'completed' OR 'COMPLETED'
        response = table.scan(
            FilterExpression=Attr('status').eq('completed') | Attr('status').eq('COMPLETED')
        )
        
        all_completed = response.get('Items', [])
        candidates = []
        
        # 2. FILTER IN PYTHON (Safe for missing columns)
        for item in all_completed:
            # If isReviewed is True (or 1), skip
            # We convert to str() just in case it's stored as "1" or "true"
            is_reviewed = item.get('isReviewed')
            if is_reviewed is True or str(is_reviewed).lower() in ['true', '1']:
                continue
            
            # If reminderSent is True, skip
            is_reminded = item.get('reminderSent')
            if is_reminded is True or str(is_reminded).lower() in ['true', '1']:
                continue
                
            candidates.append(item)

        print(f"🔍 Found {len(candidates)} potential candidates.")
        
        sent_count = 0
        
        for booking in candidates:
            try:
                # 3. CHECK AGE
                ref_date_str = booking.get('updatedAt') or booking.get('scheduledDate')
                
                if not ref_date_str:
                    print(f"⚠️ Skipping {booking['bookingId']}: No date found")
                    continue

                # Handle various Date Formats safely
                try:
                    if "T" in ref_date_str:
                        ref_date = datetime.fromisoformat(ref_date_str)
                    elif " " in ref_date_str: # Handle "2025-12-04 12:00:00" format
                         ref_date = datetime.strptime(ref_date_str, "%Y-%m-%d %H:%M:%S")
                    else:
                        ref_date = datetime.strptime(ref_date_str, "%Y-%m-%d")
                except ValueError:
                    print(f"❌ Date Error for {booking['bookingId']}: Could not parse '{ref_date_str}'")
                    continue

                # Handle Timezones
                if ref_date.tzinfo is None:
                    now = datetime.now()
                else:
                    now = datetime.now(ref_date.tzinfo)

                age = now - ref_date
                
                # 4. AGE CHECK (Must be > 24 hours)
                if age < timedelta(hours=24):
                    print(f"⏳ Skipping {booking['bookingId']}: Too new ({age})")
                    continue

                # 5. SEND EMAIL
                cust_email = booking.get('customerEmail')
                cust_id = booking.get('customerId')
                provider_name = booking.get('providerName', 'The Provider')
                review_link = f"{CLOUDFRONT_URL}?customerId={cust_id}"
                
                if not cust_email:
                    print(f"⚠️ Skipping {booking['bookingId']}: No email")
                    continue

                print(f"📧 Sending email to {cust_email}...")
                
                ses_client.send_email(
                    Source=SENDER_DISPLAY_NAME,
                    Destination={'ToAddresses': [cust_email]},
                    Message={
                        'Subject': {'Data': f"Reminder: How was your experience with {provider_name}?"},
                        'Body': {'Html': {'Data': f"""
                            <h2>We'd love your feedback!</h2>
                            <p>Hi {booking.get('customerName', 'Customer')},</p>
                            <p>It's been a couple of days since your service with <strong>{provider_name}</strong>.</p>
                            <p>If you have a moment, please leave a review to help your neighbors find great pros.</p>
                            <p style="margin: 20px 0;">
                                <a href="{review_link}" style="background:#ff9900;color:white;padding:12px 24px;text-decoration:none;border-radius:5px;font-weight:bold;">
                                ⭐ Leave a Review Now
                                </a>
                            </p>
                            <p><small>Link: {review_link}</small></p>
                        """}}
                    }
                )
                
                # 6. MARK AS SENT
                table.update_item(
                    Key={'bookingId': booking['bookingId']},
                    UpdateExpression="SET reminderSent = :t",
                    ExpressionAttributeValues={':t': True}
                )
                
                print(f"✅ Reminder sent & flagged for {cust_email}")
                sent_count += 1

            except Exception as inner_e:
                print(f"❌ Error processing booking {booking.get('bookingId')}: {inner_e}")

        return {
            'statusCode': 200,
            'body': json.dumps(f"Job Complete. Sent {sent_count} reminders.")
        }

    except Exception as e:
        print(f"❌ Critical Error: {e}")
        return {'statusCode': 500, 'body': str(e)}
