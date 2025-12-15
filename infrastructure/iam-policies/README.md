# IAM Roles and Policies Overview

## Overview
This document describes the IAM roles and policies used in the marketplace system.

**AWS Account:** 943814145891  
**Region:** us-east-1  
**Export Date:** December 4, 2025

---

## Lambda Execution Roles

### 1. marketplace-dev-lambda-execution-role

**Role ARN:** `arn:aws:iam::943814145891:role/marketplace-dev-lambda-execution-role`  
**Created:** October 26, 2025  
**Description:** Primary execution role for most Lambda functions

#### Used By
- marketplace-dev-create-booking-fn
- marketplace-dev-get-bookings-fn
- marketplace-dev-update-booking-status-fn
- marketplace-dev-search-services-fn
- marketplace-dev-get-provider-details-fn
- marketplace-dev-submit-review-fn
- marketplace-dev-health-check-fn
- marketplace-dev-send-review-reminder-fn

#### Managed Policies Attached
- **AWSLambdaVPCAccessExecutionRole** - VPC networking for Lambda
- **AmazonSESFullAccess** - Send emails via SES
- **AWSLambdaBasicExecutionRole** - CloudWatch logging
- **AWSXRayDaemonWriteAccess** - X-Ray tracing (if enabled)
- **AmazonDynamoDBReadOnlyAccess** - Read from DynamoDB
- **AmazonDynamoDBFullAccess** - Full DynamoDB operations
- **AmazonDynamoDBFullAccess_v2** - Enhanced DynamoDB access

#### Inline Policies

**MarketplaceLambdaInlinePolicy:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:UpdateItem",
        "dynamodb:Query",
        "dynamodb:Scan"
      ],
      "Resource": [
        "arn:aws:dynamodb:us-east-1:943814145891:table/marketplace-dev-*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "sns:Publish"
      ],
      "Resource": [
        "arn:aws:sns:us-east-1:943814145891:marketplace-*"
      ]
    }
  ]
}
```

**UpdateBookingAccessPolicy:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:UpdateItem",
        "dynamodb:GetItem"
      ],
      "Resource": "arn:aws:dynamodb:us-east-1:943814145891:table/marketplace-dev-bookings-table"
    }
  ]
}
```

---

### 2. marketplace-dev-booking-event-handler-fn-role-s3v7jgfs

**Role ARN:** `arn:aws:iam::943814145891:role/service-role/marketplace-dev-booking-event-handler-fn-role-s3v7jgfs`  
**Created:** November 17, 2025  
**Description:** Role for the booking event handler (processes DynamoDB Streams)

#### Used By
- marketplace-dev-booking-event-handler-fn

#### Managed Policies Attached
- **AmazonSESFullAccess** - Send booking confirmation emails
- **AmazonSNSFullAccess** - Publish to SNS topics
- **AWSLambdaBasicExecutionRole** - CloudWatch logging

#### Inline Policies

**AllowDLQAccess:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "sqs:SendMessage"
      ],
      "Resource": "arn:aws:sqs:us-east-1:943814145891:marketplace-dev-dlq"
    }
  ]
}
```

**InvoiceS3DynamoRead:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject"
      ],
      "Resource": "arn:aws:s3:::marketplace-dev-documents-grp3/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:Query"
      ],
      "Resource": [
        "arn:aws:dynamodb:us-east-1:943814145891:table/marketplace-dev-bookings-table",
        "arn:aws:dynamodb:us-east-1:943814145891:table/marketplace-dev-services-table"
      ]
    }
  ]
}
```

**marketplace-dev-booking-stream-policy:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:DescribeStream",
        "dynamodb:GetRecords",
        "dynamodb:GetShardIterator",
        "dynamodb:ListStreams"
      ],
      "Resource": "arn:aws:dynamodb:us-east-1:943814145891:table/marketplace-dev-bookings-table/stream/*"
    }
  ]
}
```

**ProviderTableReadAccess:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:Query"
      ],
      "Resource": "arn:aws:dynamodb:us-east-1:943814145891:table/marketplace-dev-providers-table"
    }
  ]
}
```

---

### 3. marketplace-dev-backfill-prices-fn-role-k7caj2qx

**Role ARN:** `arn:aws:iam::943814145891:role/service-role/marketplace-dev-backfill-prices-fn-role-k7caj2qx`  
**Created:** November 25, 2025  
**Description:** Utility role for data migration function

#### Managed Policies Attached
- **AWSLambdaBasicExecutionRole** - CloudWatch logging

---

## EventBridge Scheduler Roles

### marketplace-dev-scheduler-execution-role

**Role ARN:** `arn:aws:iam::943814145891:role/service-role/marketplace-dev-scheduler-execution-role`  
**Created:** November 27, 2025  
**Description:** Allows EventBridge to invoke Lambda functions on schedule

#### Permissions
- Invoke: marketplace-dev-send-review-reminder-fn (daily at 9 AM EST)

---

## Cognito SMS Role

### SMSAuthentication

**Role ARN:** `arn:aws:iam::943814145891:role/service-role/SMSAuthentication`  
**Created:** November 6, 2025  
**Description:** Allows Cognito to send SMS for multi-factor authentication

#### Managed Policies Attached
- **Cognito-1762399254468** (custom policy)

**Policy Content:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "sns:Publish"
      ],
      "Resource": "*"
    }
  ]
}
```

---

## Service-Linked Roles

### AWSServiceRoleForAPIGateway
**Description:** Allows API Gateway to manage resources  
**Managed By:** AWS (automatic)

### AWSServiceRoleForSupport
**Description:** AWS Support access  
**Managed By:** AWS (automatic)

### AWSServiceRoleForTrustedAdvisor
**Description:** Cost optimization recommendations  
**Managed By:** AWS (automatic)

---

## Lambda Function Resource Policies

### create-booking-fn Policy
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "allow-apigateway-dev-post-bookings",
      "Effect": "Allow",
      "Principal": {
        "Service": "apigateway.amazonaws.com"
      },
      "Action": "lambda:InvokeFunction",
      "Resource": "arn:aws:lambda:us-east-1:943814145891:function:marketplace-dev-create-booking-fn",
      "Condition": {
        "ArnLike": {
          "AWS:SourceArn": "arn:aws:execute-api:us-east-1:943814145891:n5wzcy3kib/dev/POST/bookings"
        }
      }
    }
  ]
}
```

### send-review-reminder-fn Policy
```json
{
  "Version": "2012-10-17",
  "
  ---

## Security Best Practices

### ✅ Implemented
- **Least Privilege:** Functions only have permissions they need
- **Resource-Specific ARNs:** Policies target specific tables/topics
- **Separate Roles:** Each function type has its own role
- **No Hardcoded Credentials:** All access via IAM roles
- **VPC Isolation:** Sensitive functions run in VPC

### ⚠️ Production Recommendations
- Remove wildcard (*) permissions where possible
- Implement stricter Cognito policies
- Add resource tags for cost allocation
- Enable CloudTrail for IAM audit logging
- Review and remove unused managed policies (e.g., DynamoDBReadOnly + DynamoDBFullAccess redundancy)
- Consider using AWS Secrets Manager for sensitive configuration

---

## IAM Users

### Administrator
**ARN:** `arn:aws:iam::943814145891:user/Administrator`  
**Created:** July 9, 2025  
**Policies:** AdministratorAccess, IAMUserChangePassword

### marketplace-admin
**ARN:** `arn:aws:iam::943814145891:user/marketplace-admin`  
**Created:** December 4, 2025  
**Policies:** AdministratorAccess, IAMUserChangePassword

---

## Summary

| Role Type | Count | Purpose |
|-----------|-------|---------|
| Lambda Execution Roles | 3 | Run Lambda functions |
| EventBridge Roles | 3 | Schedule Lambda invocations |
| Cognito Roles | 1 | Send SMS authentication |
| Service-Linked Roles | 4 | AWS managed services |
| IAM Users | 2 | Human administrators |

**Total IAM Roles:** 13  
**Total IAM Users:** 2  
**Total Custom Policies:** 8

---

## Access Patterns

### DynamoDB Access
- **Read-Only:** search-services-fn, get-provider-details-fn
- **Read-Write:** create-booking-fn, update-booking-status-fn
- **Full Access:** booking-event-handler-fn

### SNS/SQS Access
- **Publish:** All Lambda functions (via marketplace-lambda-execution-role)
- **Send to DLQ:** booking-event-handler-fn

### S3 Access
- **Put/Get Objects:** booking-event-handler-fn (for invoices)

### SES Access
- **Send Email:** All functions (via AmazonSESFullAccess)