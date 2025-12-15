# DynamoDB Tables Configuration

## Overview
This document describes the 6 DynamoDB tables used in the marketplace system, extracted from the actual AWS deployment.

**AWS Account:** 943814145891  
**Region:** us-east-1  
**Billing Mode:** PAY_PER_REQUEST (On-Demand)  
**Export Date:** December 4, 2025

---

## 1. marketplace-dev-bookings-table

**Table ARN:** `arn:aws:dynamodb:us-east-1:943814145891:table/marketplace-dev-bookings-table`  
**Created:** October 23, 2025  
**Item Count:** 73 bookings  
**Table Size:** 30,199 bytes

### Primary Key
- **Partition Key:** `bookingId` (String)

### Attributes
- `bookingId` (S) - Primary key
- `customerId` (S) - Customer identifier
- `providerId` (S) - Service provider identifier
- `scheduledDate` (S) - Appointment date
- `status` (S) - Booking status
- `createdAt` (S) - Creation timestamp

### Global Secondary Indexes

**1. providerBookings-index**
- **Partition Key:** `providerId` (S)
- **Sort Key:** `scheduledDate` (S)
- **Projection:** ALL
- **Purpose:** Query all bookings for a specific provider sorted by date
- **Status:** ACTIVE
- **Item Count:** 71

**2. customerBookings-index**
- **Partition Key:** `customerId` (S)
- **Sort Key:** `createdAt` (S)
- **Projection:** ALL
- **Purpose:** Query booking history for a customer
- **Status:** ACTIVE
- **Item Count:** 72

**3. status-index**
- **Partition Key:** `status` (S)
- **Sort Key:** `createdAt` (S)
- **Projection:** ALL
- **Purpose:** Find bookings by status (for admin dashboard)
- **Status:** ACTIVE
- **Item Count:** 72

**4. customerId-index**
- **Partition Key:** `customerId` (S)
- **Projection:** ALL
- **Purpose:** Additional customer lookup index
- **Status:** ACTIVE
- **Item Count:** 72

### Advanced Features
- ✅ **DynamoDB Streams:** ENABLED
  - Stream Type: NEW_AND_OLD_IMAGES
  - Stream ARN: `arn:aws:dynamodb:us-east-1:943814145891:table/marketplace-dev-bookings-table/stream/2025-11-17T05:40:38.897`
  - Purpose: Triggers Lambda for event-driven processing

- ✅ **Point-in-Time Recovery (PITR):** ENABLED
  - Recovery Period: 35 days
  - Earliest Restore: October 30, 2025
  - Latest Restore: December 4, 2025
  - Purpose: Protects against accidental data loss

- ❌ **TTL:** DISABLED

### Performance
- **Billing Mode:** On-Demand (no capacity planning needed)
- **Read/Write Capacity:** Auto-scales based on demand
- **Warm Throughput:** 12,000 read units/sec, 4,000 write units/sec

---

## 2. marketplace-dev-idempotency-table

**Table ARN:** `arn:aws:dynamodb:us-east-1:943814145891:table/marketplace-dev-idempotency-table`  
**Created:** October 23, 2025  
**Item Count:** 0 (keys auto-expire)  
**Table Size:** 0 bytes

### Primary Key
- **Partition Key:** `idempotencyKey` (String)

### Attributes
- `idempotencyKey` (S) - Unique request identifier
- `result` (S) - Cached response (JSON)
- `ttl` (N) - Unix timestamp for expiration

### Advanced Features
- ✅ **TTL:** ENABLED
  - Attribute: `ttl`
  - Purpose: Automatically deletes expired keys after 24 hours
  - Keeps storage costs low

- ✅ **Point-in-Time Recovery (PITR):** ENABLED
  - Recovery Period: 35 days

### Purpose
Implements idempotency pattern to prevent duplicate booking creation. When a client retries a failed request, the Lambda checks this table and returns the cached result instead of creating a duplicate booking.

---

## 3. marketplace-dev-services-table

**Table ARN:** `arn:aws:dynamodb:us-east-1:943814145891:table/marketplace-dev-services-table`  
**Created:** October 23, 2025  
**Item Count:** 25 services  
**Table Size:** 6,889 bytes

### Primary Key
- **Partition Key:** `serviceId` (String)

### Attributes
- `serviceId` (S) - Primary key
- `providerId` (S) - Provider offering the service
- `category` (S) - Service category (e.g., "Plumbing", "Electrical")
- `price` (N) - Service price

### Global Secondary Indexes

**1. category-index**
- **Partition Key:** `category` (S)
- **Sort Key:** `price` (N)
- **Projection:** ALL
- **Purpose:** Search services by category and sort by price
- **Status:** ACTIVE
- **Item Count:** 25

**2. providerServices-index**
- **Partition Key:** `providerId` (S)
- **Sort Key:** `price` (N)
- **Projection:** ALL
- **Purpose:** List all services offered by a specific provider
- **Status:** ACTIVE
- **Item Count:** 25

### Advanced Features
- ✅ **Point-in-Time Recovery (PITR):** ENABLED
- ❌ **TTL:** DISABLED

---

## 4. marketplace-dev-providers-table

**Table ARN:** `arn:aws:dynamodb:us-east-1:943814145891:table/marketplace-dev-providers-table`  
**Created:** October 23, 2025  
**Item Count:** 5 providers  
**Table Size:** 1,723 bytes

### Primary Key
- **Partition Key:** `providerId` (String)

### Attributes
- `providerId` (S) - Primary key
- `serviceArea` (S) - Geographic service area
- `serviceType` (S) - Type of services offered
- `rating` (N) - Average rating score
- `responseTime` (N) - Average response time
- `isAvailable` (S) - Availability status

### Global Secondary Indexes

**1. serviceType-index**
- **Partition Key:** `serviceType` (S)
- **Sort Key:** `rating` (N)
- **Projection:** ALL
- **Purpose:** Find providers by service type sorted by rating
- **Status:** ACTIVE
- **Item Count:** 5

**2. location-index**
- **Partition Key:** `serviceArea` (S)
- **Sort Key:** `rating` (N)
- **Projection:** ALL
- **Purpose:** Find providers by location sorted by rating
- **Status:** ACTIVE
- **Item Count:** 5

**3. availability-index**
- **Partition Key:** `isAvailable` (S)
- **Sort Key:** `responseTime` (N)
- **Projection:** ALL
- **Purpose:** List available providers sorted by response time
- **Status:** ACTIVE
- **Item Count:** 5

### Advanced Features
- ✅ **Point-in-Time Recovery (PITR):** ENABLED
- ❌ **TTL:** DISABLED

---

## 5. marketplace-dev-reviews-table

**Table ARN:** `arn:aws:dynamodb:us-east-1:943814145891:table/marketplace-dev-reviews-table`  
**Created:** October 23, 2025  
**Item Count:** 20 reviews  
**Table Size:** 4,143 bytes

### Primary Key
- **Partition Key:** `reviewId` (String)

### Attributes
- `reviewId` (S) - Primary key
- `bookingId` (S) - Associated booking
- `providerId` (S) - Provider being reviewed
- `createdAt` (S) - Review timestamp

### Global Secondary Indexes

**1. providerReviews-index**
- **Partition Key:** `providerId` (S)
- **Sort Key:** `createdAt` (S)
- **Projection:** ALL
- **Purpose:** Fetch all reviews for a provider (for rating calculation)
- **Status:** ACTIVE
- **Item Count:** 20

**2. bookingReviews-index**
- **Partition Key:** `bookingId` (S)
- **Projection:** ALL
- **Purpose:** Ensure one review per booking (prevents review bombing)
- **Status:** ACTIVE
- **Item Count:** 20

### Advanced Features
- ✅ **Point-in-Time Recovery (PITR):** ENABLED
- ❌ **TTL:** DISABLED

---

## 6. marketplace-dev-users-table

**Table ARN:** `arn:aws:dynamodb:us-east-1:943814145891:table/marketplace-dev-users-table`  
**Created:** October 23, 2025  
**Item Count:** 0  
**Table Size:** 0 bytes

### Primary Key
- **Partition Key:** `userId` (String)

### Attributes
- `userId` (S) - Primary key (matches Cognito sub)
- `email` (S) - User email address
- `userType` (S) - "CUSTOMER" or "PROVIDER"
- `createdAt` (S) - Account creation timestamp

### Global Secondary Indexes

**1. email-index**
- **Partition Key:** `email` (S)
- **Projection:** ALL
- **Purpose:** Look up user by email address
- **Status:** ACTIVE
- **Item Count:** 0

**2. userType-index**
- **Partition Key:** `userType` (S)
- **Sort Key:** `createdAt` (S)
- **Projection:** ALL
- **Purpose:** Segment users by type (for admin queries, marketing)
- **Status:** ACTIVE
- **Item Count:** 0

### Advanced Features
- ✅ **Point-in-Time Recovery (PITR):** ENABLED
- ❌ **TTL:** DISABLED

### Purpose
Extends AWS Cognito identity with application-specific profile data. The `userId` matches Cognito's `sub` attribute, creating a hard link between authentication and application profile.

---

## Summary Table

| Table Name | Items | Size | Streams | PITR | TTL | GSIs |
|------------|-------|------|---------|------|-----|------|
| bookings-table | 73 | 30 KB | ✅ | ✅ | ❌ | 4 |
| idempotency-table | 0 | 0 KB | ❌ | ✅ | ✅ | 0 |
| services-table | 25 | 7 KB | ❌ | ✅ | ❌ | 2 |
| providers-table | 5 | 2 KB | ❌ | ✅ | ❌ | 3 |
| reviews-table | 20 | 4 KB | ❌ | ✅ | ❌ | 2 |
| users-table | 0 | 0 KB | ❌ | ✅ | ❌ | 2 |

**Total Storage:** ~43 KB  
**Total Items:** 123  
**Total GSIs:** 13

---

## Design Patterns Used

### 1. Event-Driven Architecture
The `bookings-table` uses DynamoDB Streams to trigger Lambda functions asynchronously, enabling real-time event processing without tight coupling.

### 2. Idempotency Pattern
The `idempotency-table` prevents duplicate operations by caching request results with automatic cleanup via TTL.

### 3. Access Pattern Optimization
Each GSI is designed for a specific query pattern, avoiding expensive table scans:
- Customer queries: `customerBookings-index`
- Provider queries: `providerBookings-index`
- Admin queries: `status-index`

### 4. Single-Digit Latency
On-Demand billing mode ensures consistent millisecond response times without capacity planning.

---

## Cost Optimization

**Current Costs:** Running on AWS Free Tier
- **Storage:** ~43 KB (well under 25 GB free tier)
- **Reads/Writes:** Minimal usage (well under 200M requests/month free tier)
- **Backup:** PITR enabled (no additional cost for standard recovery)

**Production Recommendations:**
- Monitor actual usage with CloudWatch
- Consider Provisioned Capacity if traffic becomes predictable
- Use DynamoDB auto-scaling for cost-optimized performance