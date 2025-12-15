import json
import boto3
from boto3.dynamodb.conditions import Key

def lambda_handler(event, context):
    print("DEBUG: Incoming event ->", json.dumps(event))

    try:
        # Extract query parameters
        params = event.get("queryStringParameters", {}) or {}
        customer_id = params.get("customerId")
        provider_id = params.get("providerId")

        # Validate required parameters
        if not customer_id and not provider_id:
            return {
                "statusCode": 400,
                "headers": {
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "GET,OPTIONS",
                    "Access-Control-Allow-Headers": "Content-Type,Authorization"
                },
                "body": json.dumps({
                    "error": "Missing customerId or providerId parameter"
                })
            }

        # Initialize DynamoDB table
        dynamodb = boto3.resource("dynamodb")
        table = dynamodb.Table("marketplace-dev-bookings-table")

        # ✅ Handle either customer or provider-based queries
        if customer_id:
            index_name = "customerId-index"
            key_expr = Key("customerId").eq(customer_id)
        else:
            index_name = "providerBookings-index"
            key_expr = Key("providerId").eq(provider_id)

        response = table.query(
            IndexName=index_name,
            KeyConditionExpression=key_expr
        )

        items = response.get("Items", [])
        print("DEBUG: DynamoDB returned {} items".format(len(items)))

        # ✅ Normalize data for frontend (fix .toFixed() and nulls)
        for item in items:
            # Convert numeric strings to floats
            if "servicePrice" in item:
                try:
                    item["servicePrice"] = float(item["servicePrice"])
                except Exception:
                    item["servicePrice"] = 0.0

            # Normalize date/time or numeric fields if missing
            for k, v in item.items():
                if v is None:
                    item[k] = ""

        # ✅ Return structured response
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET,OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type,Authorization"
            },
            "body": json.dumps({"bookings": items}, default=str)
        }

    except Exception as e:
        print("ERROR:", str(e))
        return {
            "statusCode": 500,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET,OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type,Authorization"
            },
            "body": json.dumps({"error": str(e)})
        }
