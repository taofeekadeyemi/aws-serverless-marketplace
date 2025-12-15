import json

import boto3

import os

import botocore

from datetime import datetime



# Initialize AWS clients

dynamodb = boto3.resource("dynamodb")

table = dynamodb.Table("marketplace-dev-bookings-table")

sns = boto3.client("sns")



# SNS Topic ARN (prefer environment variable)

SNS_TOPIC_ARN = os.environ.get(

    "SNS_TOPIC_ARN",

    "arn:aws:sns:us-east-1:943814145891:marketplace-dev-provider-updates"

)

print("SNS Topic being used:", SNS_TOPIC_ARN)

def lambda_handler(event, context):

    print("Incoming event:", json.dumps(event))



    headers = {

        "Content-Type": "application/json",

        "Access-Control-Allow-Origin": "*",

        "Access-Control-Allow-Methods": "PUT,OPTIONS",

        "Access-Control-Allow-Headers": "Content-Type,Authorization"

    }



    try:

        # Extract path and body

        booking_id = event.get("pathParameters", {}).get("bookingId")

        body = json.loads(event.get("body") or "{}")

        new_status = body.get("status", "").lower()



        if not booking_id or not new_status:

            return {

                "statusCode": 400,

                "headers": headers,

                "body": json.dumps({

                    "status": "error",

                    "message": "bookingId and status are required"

                })

            }



        # Validate allowed statuses

        valid_statuses = [

            "pending_confirmation", "confirmed", "in_progress",

            "completed", "cancelled", "paid"

        ]

        if new_status not in valid_statuses:

            return {

                "statusCode": 400,

                "headers": headers,

                "body": json.dumps({

                    "status": "error",

                    "message": f"Invalid status '{new_status}'. Must be one of {valid_statuses}"

                })

            }



        # Extract provider info from JWT

        claims = event.get("requestContext", {}).get("authorizer", {}).get("claims", {})

        provider_id = claims.get("custom:providerId", "")

        user_email = claims.get("email", "")

        user_groups = claims.get("cognito:groups", "")



        print("🔍 DEBUG FULL CLAIMS:", json.dumps(claims, indent=2))

        print("🔍 provider_id:", provider_id)

        print("🔍 user_groups:", user_groups)



        # Retrieve booking

        existing = table.get_item(Key={"bookingId": booking_id})

        booking = existing.get("Item")



        if not booking:

            return {

                "statusCode": 404,

                "headers": headers,

                "body": json.dumps({

                    "status": "error",

                    "message": "Booking not found"

                })

            }



        # Admins can update anything; providers only their own

        is_admin = "Admins" in user_groups

        if not is_admin and booking.get("providerId") != provider_id:

            return {

                "statusCode": 403,

                "headers": headers,

                "body": json.dumps({

                    "status": "error",

                    "message": "Access denied: You can only update your own bookings"

                })

            }



        # Update booking

        print(f"DEBUG: Updating booking '{booking_id}' to '{new_status}' by '{provider_id}'")

        table.update_item(

            Key={"bookingId": booking_id},

            UpdateExpression="SET #s = :s, updatedAt = :u, updatedBy = :by",

            ExpressionAttributeNames={"#s": "status"},

            ExpressionAttributeValues={

                ":s": new_status,

                ":u": datetime.utcnow().isoformat(),

                ":by": user_email or provider_id

            }

        )



        # 👉 Send SNS notification for EVERY update

        try:

            message = (

                f"Booking {booking_id} status has been updated.\n"

                f"New status: {new_status.upper()}\n"

                f"Updated by: {user_email or provider_id}"

            )



            sns.publish(

                TopicArn=SNS_TOPIC_ARN,

                Message=message,

                Subject=f"Booking Status Updated: {new_status.upper()}"

            )

            print(f"✅ SNS notification sent for booking {booking_id}")



        except botocore.exceptions.EndpointConnectionError as e:

            print("⚠️ SNS network connection issue:", str(e))

        except botocore.exceptions.ClientError as e:

            print("⚠️ SNS publish failed:", str(e))

        except Exception as sns_err:

            print("⚠️ Unexpected SNS error:", str(sns_err))



        # Success

        return {

            "statusCode": 200,

            "headers": headers,

            "body": json.dumps({

                "status": "success",

                "message": f"Booking status updated to '{new_status}'",

                "bookingId": booking_id

            })

        }



    except Exception as e:

        print("ERROR:", str(e))

        import traceback

        print(traceback.format_exc())

        return {

            "statusCode": 500,

            "headers": headers,

            "body": json.dumps({

                "status": "error",

                "message": "Internal server error",

                "error": str(e)

            })

        }
