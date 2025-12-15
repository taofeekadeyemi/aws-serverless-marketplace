import json
import boto3
import uuid
from datetime import datetime
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('marketplace-dev-bookings-table') 

def lambda_handler(event, context):
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,Authorization',
        'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
    }

    if event['httpMethod'] == 'OPTIONS':
        return {'statusCode': 200, 'headers': headers, 'body': json.dumps('CORS OK')}

    if event['httpMethod'] == 'POST':
        try:
            # DEBUG: Print what we received
            print("📥 Received Body:", event['body'])
            
            body = json.loads(event['body'])
            booking_id = str(uuid.uuid4())
            
            # Extract and Cast Data
            # We use Decimal for price to make DynamoDB happy
            price_input = body.get('servicePrice', 0)
            price_decimal = Decimal(str(price_input)) if price_input else Decimal(0)

            item = {
                'bookingId': booking_id,
                'serviceId': body.get('serviceId'),
                'customerId': body.get('customerId'),
                'customerName': body.get('customerName'),
                'customerEmail': body.get('customerEmail', ''), 
                'customerPhone': body.get('customerPhone'),
                'customerAddress': body.get('customerAddress'),
                'scheduledDate': body.get('scheduledDate'),
                'notes': body.get('notes', ''),
                'providerId': body.get('providerId'),
                
                # 🟢 CRITICAL FIELDS
                'providerName': body.get('providerName', 'Unknown Provider'),
                'serviceName': body.get('serviceName', 'Unknown Service'), 
                'servicePrice': price_decimal,
                
                'status': 'PENDING',
                'createdAt': datetime.now().isoformat()
            }

            print("💾 Saving Item:", json.dumps(str(item))) # Debug print
            table.put_item(Item=item)

            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({
                    'message': 'Booking created successfully',
                    'bookingId': booking_id,
                    'providerName': item['providerName']
                })
            }

        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return {
                'statusCode': 500,
                'headers': headers,
                'body': json.dumps(f"Server Error: {str(e)}")
            }

    return {'statusCode': 400, 'headers': headers, 'body': json.dumps('Unsupported method')}
