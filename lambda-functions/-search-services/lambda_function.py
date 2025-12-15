import json
import boto3
from boto3.dynamodb.conditions import Key
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('marketplace-dev-services-table')

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal): return float(obj)
        return super(DecimalEncoder, self).default(obj)

def lambda_handler(event, context):
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Methods': 'GET,OPTIONS'
    }
    
    if event.get('httpMethod') == 'OPTIONS':
        return {"statusCode": 200, "headers": headers}

    try:
        params = event.get('queryStringParameters') or {}
        category = params.get('category')
        location = params.get('location')
        max_price = params.get('maxPrice')

        if not category:
            return {"statusCode": 400, "headers": headers, "body": json.dumps({"message": "Category required"})}

        # 1. Query Services Table
        key_condition = Key('category').eq(category)
        if max_price:
            key_condition = key_condition & Key('price').lte(Decimal(max_price))

        response = table.query(
            IndexName='category-index',
            KeyConditionExpression=key_condition
        )
        services = response.get('Items', [])

        # 2. Filter by Location
        if location:
            loc_lower = location.lower()
            services = [s for s in services if 'providerName' in s and loc_lower in s.get('providerName', '').lower()]

        # 3. Filter Availability
        services = [s for s in services if s.get('availability') == 'available']

        return {
            "statusCode": 200,
            "headers": headers,
            "body": json.dumps({"services": services, "count": len(services)}, cls=DecimalEncoder)
        }

    except Exception as e:
        return {"statusCode": 500, "headers": headers, "body": json.dumps({"error": str(e)})}
