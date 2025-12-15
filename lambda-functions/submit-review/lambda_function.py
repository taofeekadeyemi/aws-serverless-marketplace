import json
import boto3
import uuid
from datetime import datetime
from decimal import Decimal

# --- Configuration ---
REVIEWS_TABLE_NAME = "marketplace-dev-reviews-table"
BOOKINGS_TABLE_NAME = "marketplace-dev-bookings-table"
SERVICES_TABLE_NAME = "marketplace-dev-services-table"
REVIEWS_INDEX_NAME = "providerReviews-index"

# --- Clients ---
dynamodb = boto3.resource('dynamodb')
reviews_table = dynamodb.Table(REVIEWS_TABLE_NAME)
bookings_table = dynamodb.Table(BOOKINGS_TABLE_NAME)
services_table = dynamodb.Table(SERVICES_TABLE_NAME)

def lambda_handler(event, context):
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type",
        "Access-Control-Allow-Methods": "POST, OPTIONS"
    }

    if event.get('httpMethod') == 'OPTIONS':
        return {"statusCode": 200, "headers": headers, "body": ""}

    try:
        body = json.loads(event.get('body', '{}')) if isinstance(event.get('body'), str) else event
        
        booking_id = body.get('bookingId')
        rating = body.get('rating')
        comment = body.get('comment')
        
        if not all([booking_id, rating]):
            return {"statusCode": 400, "headers": headers, "body": json.dumps({"message": "Missing fields"})}

        # 1. Fetch Booking
        booking_resp = bookings_table.get_item(Key={'bookingId': booking_id})
        if 'Item' not in booking_resp:
            return {"statusCode": 404, "headers": headers, "body": json.dumps({"message": "Booking not found"})}
            
        booking_item = booking_resp['Item']
        provider_id = booking_item.get('providerId')
        service_id = booking_item.get('serviceId')
        reviewer_name = booking_item.get('customerName', 'Anonymous')

        # 2. Save Review
        review_id = str(uuid.uuid4())
        new_review = {
            'reviewId': review_id,
            'bookingId': booking_id,
            'providerId': provider_id,
            'serviceId': service_id, # 🟢 IMPORTANT: We use this to filter later
            'rating': int(rating),
            'comment': comment,
            'reviewerName': reviewer_name,
            'createdAt': datetime.now().isoformat()
        }
        reviews_table.put_item(Item=new_review)

        # 3. Mark Booking as Reviewed
        bookings_table.update_item(Key={'bookingId': booking_id}, UpdateExpression="SET isReviewed = :r", ExpressionAttributeValues={':r': True})

        # 4. 🟢 INTELLIGENT AGGREGATION 🟢
        from boto3.dynamodb.conditions import Key
        
        # Query all reviews for this provider
        reviews_resp = reviews_table.query(
            IndexName=REVIEWS_INDEX_NAME,
            KeyConditionExpression=Key('providerId').eq(provider_id)
        )
        
        all_items = reviews_resp.get('Items', [])
        if not any(r['reviewId'] == review_id for r in all_items):
            all_items.append(new_review)

        # 🟢 FILTER: Keep ONLY reviews for this specific Service ID
        service_reviews = [r for r in all_items if r.get('serviceId') == service_id]

        # Calculate Stats based on Filtered List
        count = len(service_reviews)
        if count > 0:
            total_score = sum(int(r['rating']) for r in service_reviews)
            avg_rating = round(total_score / count, 1)
        else:
            avg_rating = 0
        
        # Sort & Slice
        service_reviews.sort(key=lambda x: x['createdAt'], reverse=True)
        latest_5 = service_reviews[:5]
        
        embedded_reviews = [
            {
                'reviewerName': r.get('reviewerName', 'Customer'),
                'rating': int(r['rating']),
                'comment': r.get('comment', ''),
                'date': r.get('createdAt', '').split('T')[0]
            }
            for r in latest_5
        ]

        # 5. Update Service Table
        if service_id:
            services_table.update_item(
                Key={'serviceId': service_id},
                UpdateExpression="SET rating = :r, reviewCount = :c, reviews = :l",
                ExpressionAttributeValues={
                    ':r': Decimal(str(avg_rating)),
                    ':c': count,
                    ':l': embedded_reviews
                }
            )

        return {
            "statusCode": 200,
            "headers": headers,
            "body": json.dumps({"message": "Review submitted and service updated!"})
        }

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return {"statusCode": 500, "headers": headers, "body": json.dumps({"message": str(e)})}
