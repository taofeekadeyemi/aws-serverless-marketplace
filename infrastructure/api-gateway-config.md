# API Gateway Configuration

## Overview
REST API serving as the entry point for all marketplace operations.

**API ID:** n5wzcy3kib  
**API Name:** marketplace-dev-api  
**Description:** Marketplace REST API for service bookings  
**Region:** us-east-1  
**Created:** October 29, 2025  
**Endpoint Type:** Regional  
**IP Address Type:** IPv4

---

## API Endpoints

### Base URLs
- **Invoke URL:** `https://n5wzcy3kib.execute-api.us-east-1.amazonaws.com/dev`
- **Root Resource ID:** 85vke92mx3

---

## Resources & Methods

### 1. /health
**Resource ID:** 0mf1h9  
**Path:** `/health`

**GET /health**
- **Lambda:** marketplace-dev-health-check-fn
- **Authorization:** None (public endpoint)
- **Purpose:** System health monitoring
- **Response:** Returns `{"status": "healthy"}`

**OPTIONS /health**
- **Purpose:** CORS preflight

---

### 2. /services
**Resource ID:** 9jukw2  
**Path:** `/services`

**GET /services**
- **Lambda:** marketplace-dev-search-services-fn
- **Authorization:** None (public endpoint)
- **Query Parameters:**
  - `category` (optional) - Filter by service category
  - `maxPrice` (optional) - Filter by maximum price
  - `providerId` (optional) - Filter by provider
- **Purpose:** Search and browse available services
- **Response:** List of services matching criteria

**OPTIONS /services**
- **Purpose:** CORS preflight

---

### 3. /providers
**Resource ID:** snfohd  
**Path:** `/providers`

**GET /providers**
- **Lambda:** marketplace-dev-search-services-fn
- **Authorization:** None (public endpoint)
- **Query Parameters:**
  - `serviceArea` (optional) - Filter by location
  - `specialty` (optional) - Filter by specialty
- **Purpose:** Browse service providers
- **Response:** List of providers

**OPTIONS /providers**
- **Purpose:** CORS preflight

---

### 4. /providers/{providerId}
**Resource ID:** gvebaw  
**Path:** `/providers/{providerId}`

**GET /providers/{providerId}**
- **Lambda:** marketplace-dev-get-provider-details-fn
- **Authorization:** None (public endpoint)
- **Path Parameter:** `providerId` (required)
- **Purpose:** Get provider details including reviews
- **Response:** Provider profile + aggregated reviews

**OPTIONS /providers/{providerId}**
- **Purpose:** CORS preflight

---

### 5. /bookings
**Resource ID:** t4hhld  
**Path:** `/bookings`

**POST /bookings**
- **Lambda:** marketplace-dev-create-booking-fn
- **Authorization:** None (email validation in Lambda)
- **Request Body:**
```json
  {
    "customerId": "string",
    "providerId": "string",
    "serviceId": "string",
    "scheduledTime": "ISO-8601 timestamp",
    "idempotencyKey": "uuid"
  }
```
- **Purpose:** Create a new service booking
- **Response:** Booking confirmation with `bookingId`

**GET /bookings**
- **Lambda:** marketplace-dev-get-bookings-fn
- **Authorization:** AWS_IAM (Cognito)
- **Query Parameters:**
  - `userId` (required) - User identifier
  - `userType` (required) - "CUSTOMER" or "PROVIDER"
- **Purpose:** List user's bookings
- **Response:** Array of bookings

**OPTIONS /bookings**
- **Purpose:** CORS preflight

---

### 6. /bookings/{bookingId}
**Resource ID:** kweqms  
**Path:** `/bookings/{bookingId}`

**GET /bookings/{bookingId}**
- **Lambda:** marketplace-dev-get-bookings-fn
- **Authorization:** AWS_IAM (Cognito)
- **Path Parameter:** `bookingId` (required)
- **Purpose:** Get booking details
- **Response:** Single booking object

**PUT /bookings/{bookingId}**
- **Lambda:** marketplace-dev-update-booking-status-fn
- **Authorization:** AWS_IAM (Cognito - Provider only)
- **Path Parameter:** `bookingId` (required)
- **Request Body:**
```json
  {
    "status": "CONFIRMED" | "COMPLETED" | "PAID"
  }
```
- **Purpose:** Update booking (providers only)
- **Response:** Updated booking object

**OPTIONS /bookings/{bookingId}**
- **Purpose:** CORS preflight

---

### 7. /bookings/{bookingId}/status
**Resource ID:** agvazu  
**Path:** `/bookings/{bookingId}/status`

**PUT /bookings/{bookingId}/status**
- **Lambda:** marketplace-dev-update-booking-status-fn
- **Authorization:** AWS_IAM (Cognito - Provider only)
- **Path Parameter:** `bookingId` (required)
- **Request Body:**
```json
  {
    "status": "CONFIRMED" | "COMPLETED" | "PAID"
  }
```
- **Purpose:** Provider updates booking status
- **Response:** Updated booking

**OPTIONS /bookings/{bookingId}/status**
- **Purpose:** CORS preflight

---

### 8. /reviews
**Resource ID:** 3cdl2q  
**Path:** `/reviews`

**POST /reviews**
- **Lambda:** marketplace-dev-submit-review-fn
- **Authorization:** None
- **Request Body:**
```json
  {
    "bookingId": "string",
    "rating": 1-5,
    "comment": "string"
  }
```
- **Purpose:** Submit a service review
- **Response:** Review confirmation

**GET /reviews**
- **Lambda:** marketplace-dev-get-provider-details-fn
- **Authorization:** None
- **Query Parameters:**
  - `providerId` (optional) - Get reviews for provider
  - `bookingId` (optional) - Get review for booking
- **Purpose:** Fetch reviews
- **Response:** Array of reviews

**OPTIONS /reviews**
- **Purpose:** CORS preflight

---

## CORS Configuration

### Allowed Origins
`*` (all origins)  
⚠️ **Note:** In production, restrict to specific domains

### Allowed Methods
- GET
- POST
- PUT
- OPTIONS

### Allowed Headers
- Content-Type
- Authorization
- X-Amz-Date
- X-Api-Key

---

## Deployment Configuration

### Stage: dev
**Deployment ID:** tim2ta  
**Created:** October 29, 2025  
**Last Updated:** November 24, 2025  
**Stage URL:** `https://n5wzcy3kib.execute-api.us-east-1.amazonaws.com/dev`

### Settings
- **Caching:** DISABLED
- **Cache Size:** 0.5 GB (if enabled)
- **Tracing:** DISABLED
- **API Key:** Not required
- **Resource Policies:** None

---

## Throttling & Rate Limiting

### Default Limits
- **Rate:** 1,000 requests/second
- **Burst:** 2,000 requests
- **Purpose:** Prevent abuse and manage costs

### Per-Method Limits
None configured (using default)

---

## Authentication & Authorization

### Public Endpoints (No Auth)
- `GET /services`
- `GET /providers`
- `GET /providers/{providerId}`
- `POST /bookings`
- `POST /reviews`
- `GET /reviews`
- `GET /health`

### Protected Endpoints (AWS IAM via Cognito)
- `GET /bookings` - Requires authenticated user
- `GET /bookings/{bookingId}` - Requires authenticated user
- `PUT /bookings/{bookingId}` - Requires provider role
- `PUT /bookings/{bookingId}/status` - Requires provider role

### Authorization Flow
1. User authenticates via Cognito
2. Cognito returns JWT token
3. API Gateway validates token via IAM
4. Lambda function checks user permissions

---

## Monitoring

### CloudWatch Metrics
- **4XXError** - Client errors (tracked by alarm)
- **5XXError** - Server errors (tracked by alarm)
- **Count** - Total requests
- **Latency** - Response time

### CloudWatch Alarm
**Alarm Name:** marketplace-api-5xx-errors-alarm
- **Metric:** 5XXError
- **Threshold:** > 10 (average)
- **Period:** 5 minutes
- **Action:** Publishes to SNS topic `marketplace-notifications`

---

## Lambda Integration Details

| Lambda Function | Endpoints | VPC | Timeout |
|----------------|-----------|-----|---------|
| create-booking-fn | POST /bookings | ✅ | 10s |
| get-bookings-fn | GET /bookings, GET /bookings/{id} | ✅ | 3s |
| update-booking-status-fn | PUT /bookings/{id}/status | ❌ | 10s |
| search-services-fn | GET /services, GET /providers | ✅ | 3s |
| get-provider-details-fn | GET /providers/{id}, GET /reviews | ✅ | 3s |
| submit-review-fn | POST /reviews | ✅ | 3s |
| health-check-fn | GET /health | ✅ | 3s |

---

## Security Best Practices

### Implemented
✅ HTTPS enforcement (redirect-to-https)  
✅ CORS configuration  
✅ IAM authentication for sensitive endpoints  
✅ Request throttling  
✅ CloudWatch monitoring and alarms

### Recommended for Production
- [ ] Enable API caching for GET endpoints
- [ ] Implement request validation
- [ ] Add API keys for partner integrations
- [ ] Enable AWS WAF for DDoS protection
- [ ] Restrict CORS to specific domains
- [ ] Enable CloudWatch Logs for all endpoints
- [ ] Implement custom authorizer for fine-grained permissions

---

## Cost Optimization

**Current Usage:**
- Running on AWS Free Tier
- Estimated requests: ~1,000/day
- Estimated monthly cost: $0 (under free tier)

**Free Tier Limits:**
- 1 million API calls/month
- 750,000 connection minutes/month

**Monitoring:** CloudWatch dashboard tracks usage to prevent overages