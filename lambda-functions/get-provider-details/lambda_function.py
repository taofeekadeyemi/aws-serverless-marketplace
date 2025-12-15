import json
import boto3
from boto3.dynamodb.conditions import Key
from decimal import Decimal

# --- Table Configuration ---
REVIEWS_TABLE_NAME = "marketplace-dev-reviews-table"
REVIEWS_INDEX_NAME = "providerReviews-index"

dynamodb = boto3.resource("dynamodb")
reviews_table = dynamodb.Table(REVIEWS_TABLE_NAME)

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

def lambda_handler(event, context):
    headers = {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type",
        "Access-Control-Allow-Methods": "GET,OPTIONS"
    }

    # Handle preflight
    if event.get("httpMethod") == "OPTIONS":
        return {"statusCode": 200, "headers": headers, "body": ""}

    try:
        qs = event.get("queryStringParameters") or {}
        provider_id = qs.get("providerId")

        if not provider_id:
            return {
                "statusCode": 400,
                "headers": headers,
                "body": json.dumps({"message": "providerId is required"})
            }

        # 🚀 FIX: Escape DynamoDB reserved keyword "comment"
        response = reviews_table.query(
            IndexName=REVIEWS_INDEX_NAME,
            KeyConditionExpression=Key("providerId").eq(provider_id),
            ProjectionExpression="#r, #c, createdAt",
            ExpressionAttributeNames={
                "#r": "rating",
                "#c": "comment"
            }
        )

        items = response.get("Items", [])
        count = len(items)

        if count == 0:
            return {
                "statusCode": 200,
                "headers": headers,
                "body": json.dumps({
                    "reviews": [],
                    "reviewCount": 0,
                    "averageRating": 0
                })
            }

        # Calculate average rating
        total = sum(float(i.get("rating", 0)) for i in items)
        avg_rating = round(total / count, 1)

        # Sort by newest
        items.sort(key=lambda x: x.get("createdAt", ""), reverse=True)

        # Format for frontend
        reviews_list = [
            {
                "comment": i.get("comment", ""),
                "rating": float(i.get("rating", 0)),
                "date": i.get("createdAt", "").split("T")[0]
            }
            for i in items
        ]

        return {
            "statusCode": 200,
            "headers": headers,
            "body": json.dumps({
                "reviews": reviews_list,
                "reviewCount": count,
                "averageRating": avg_rating
            }, cls=DecimalEncoder)
        }

    except Exception as e:
        print("ERROR:", str(e))
        return {
            "statusCode": 500,
            "headers": headers,
            "body": json.dumps({"message": str(e)})
        }
