# API Documentation - Digital FTE Customer Success Agent

Complete API reference for integrating with the Digital FTE Customer Success Agent.

## Table of Contents

1. [Base URL](#base-url)
2. [Authentication](#authentication)
3. [Common Headers](#common-headers)
4. [Error Handling](#error-handling)
5. [Endpoints](#endpoints)
   - [Health Check](#health-check)
   - [Web Support Form](#web-support-form)
   - [Gmail Webhook](#gmail-webhook)
   - [WhatsApp Webhook](#whatsapp-webhook)
   - [Ticket Status](#ticket-status)
6. [Data Models](#data-models)
7. [Rate Limits](#rate-limits)
8. [Webhooks](#webhooks)

## Base URL

```
Production: https://api.yourdomain.com
Staging: https://staging-api.yourdomain.com
Local: http://localhost:8000
```

## Authentication

### Public Endpoints (No Authentication)
- Health checks (`/health`, `/health/liveness`, `/health/readiness`)
- Web support form (`POST /api/support`)

### Webhook Endpoints (Signature Validation)
- **Gmail**: Google Cloud Pub/Sub signature validation (automatic)
- **WhatsApp**: Twilio HMAC-SHA1 signature in `X-Twilio-Signature` header

## Common Headers

### Request Headers

```http
Content-Type: application/json
User-Agent: Your-Application/1.0.0
```

### Response Headers

```http
Content-Type: application/json
X-Request-ID: <unique-request-id>
X-Response-Time: <time-in-ms>
```

## Error Handling

### Standard Error Response

```json
{
  "error": "ErrorType",
  "message": "Human-readable error message",
  "detail": {
    "field": "email",
    "reason": "Invalid format"
  },
  "request_id": "req_1234567890"
}
```

### HTTP Status Codes

| Code | Meaning | When It Occurs |
|------|---------|----------------|
| 200 | OK | Successful request |
| 201 | Created | Resource created successfully |
| 400 | Bad Request | Invalid request data |
| 403 | Forbidden | Invalid signature (webhooks) |
| 404 | Not Found | Resource doesn't exist |
| 422 | Unprocessable Entity | Validation error |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | System error |
| 503 | Service Unavailable | System maintenance |

### Common Error Types

| Error Type | Description | HTTP Code |
|-----------|-------------|-----------|
| `ValidationError` | Request validation failed | 422 |
| `InvalidSignature` | Webhook signature invalid | 403 |
| `TicketNotFound` | Ticket ID doesn't exist | 404 |
| `RateLimitExceeded` | Too many requests | 429 |
| `InternalServerError` | System error | 500 |

---

## Endpoints

### Health Check

#### GET /health

Get overall system health status.

**Response: 200 OK**

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2026-03-20T10:30:00Z",
  "database": "connected",
  "ai_provider": "groq (llama-3.3-70b-versatile)"
}
```

**Response Fields**:
- `status` (string): Overall health status (`healthy` or `unhealthy`)
- `version` (string): API version
- `timestamp` (string): Current server time (ISO 8601)
- `database` (string): Database connection status
- `ai_provider` (string): AI provider and model information

---

#### GET /health/liveness

Kubernetes liveness probe - checks if API is running.

**Response: 200 OK**

```json
{
  "status": "alive",
  "timestamp": "2026-03-20T10:30:00Z"
}
```

---

#### GET /health/readiness

Kubernetes readiness probe - checks if API can serve traffic.

**Response: 200 OK** (ready to serve)

```json
{
  "status": "ready",
  "checks": {
    "database": "ready"
  },
  "timestamp": "2026-03-20T10:30:00Z"
}
```

**Response: 503** (not ready)

```json
{
  "status": "not ready",
  "checks": {
    "database": "error: ConnectionRefusedError"
  },
  "timestamp": "2026-03-20T10:30:00Z"
}
```

---

### Web Support Form

#### POST /api/support

Submit a customer support request via web form.

**Request Body**:

```json
{
  "name": "John Doe",
  "email": "john.doe@example.com",
  "message": "I need help resetting my password. I've tried the forgot password link but haven't received an email."
}
```

**Request Fields**:
- `name` (string, required): Customer's full name (2-255 characters)
- `email` (string, required): Customer's email address (valid email format)
- `message` (string, required): Support request message (10-5000 characters)

**Response: 201 Created**

```json
{
  "ticket_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "resolved",
  "message": "Thank you for contacting us, John! To reset your password:\n\n1. Go to https://example.com/login\n2. Click 'Forgot Password?'\n3. Enter your email: john.doe@example.com\n4. Check your inbox (and spam folder) for the reset link\n5. The link expires in 1 hour\n\nIf you still don't receive the email after 5 minutes, please check:\n- Your spam/junk folder\n- That john.doe@example.com is the correct email for your account\n\nNeed more help? Reply to this email or visit our help center at https://help.example.com",
  "estimated_response_time": "Immediate (AI-powered response)",
  "created_at": "2026-03-20T10:30:00Z"
}
```

**Response Fields**:
- `ticket_id` (string): Unique ticket identifier (UUID)
- `status` (string): Ticket status (`resolved` or `escalated`)
- `message` (string): AI-generated response to customer
- `estimated_response_time` (string): Response time estimate
- `created_at` (string): Ticket creation timestamp (ISO 8601)

**Errors**:

**422 Unprocessable Entity** (Validation Error):

```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "value is not a valid email address",
      "type": "value_error.email"
    }
  ]
}
```

**500 Internal Server Error**:

```json
{
  "error": "InternalServerError",
  "message": "Failed to process your request. Please try again.",
  "request_id": "req_1234567890"
}
```

**Example cURL**:

```bash
curl -X POST https://api.yourdomain.com/api/support \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john.doe@example.com",
    "message": "I need help resetting my password."
  }'
```

---

### Gmail Webhook

#### POST /api/webhooks/gmail

Receive Gmail notifications via Google Cloud Pub/Sub.

**Note**: This endpoint is called automatically by Google Cloud Pub/Sub when emails arrive. You should not call this endpoint directly.

**Request Body** (Pub/Sub format):

```json
{
  "message": {
    "data": "eyJlbWFpbEFkZHJlc3MiOiAic3VwcG9ydEBleGFtcGxlLmNvbSIsICJoaXN0b3J5SWQiOiAiMTIzNDU2In0=",
    "messageId": "2070443601311540",
    "publishTime": "2026-03-20T10:30:00.000Z"
  },
  "subscription": "projects/myproject/subscriptions/gmail-notifications"
}
```

**Request Fields**:
- `message.data` (string): Base64-encoded Gmail notification data
- `message.messageId` (string): Pub/Sub message ID
- `message.publishTime` (string): Message publish time
- `subscription` (string): Pub/Sub subscription name

**Response: 200 OK**

```json
{
  "status": "success",
  "message": "Email processed successfully",
  "ticket_id": "660e8400-e29b-41d4-a716-446655440001"
}
```

**Response (Error, still 200 OK)**:

```json
{
  "status": "error",
  "message": "Gmail notification processing failed",
  "ticket_id": null
}
```

**Note**: Always returns 200 OK to prevent Pub/Sub retries (errors are logged for monitoring).

---

#### GET /api/webhooks/gmail/health

Health check for Gmail webhook (for Google verification).

**Response: 200 OK**

```json
{
  "status": "healthy",
  "webhook": "gmail",
  "channel": "email",
  "timestamp": "2026-03-20T10:30:00Z"
}
```

---

### WhatsApp Webhook

#### POST /api/webhooks/whatsapp

Receive WhatsApp messages via Twilio webhook.

**Note**: This endpoint is called automatically by Twilio when WhatsApp messages arrive. Configure this URL in your Twilio console.

**Authentication**: Twilio signature validation via `X-Twilio-Signature` header.

**Request Headers**:

```http
Content-Type: application/x-www-form-urlencoded
X-Twilio-Signature: <HMAC-SHA1-signature>
```

**Request Body** (form-encoded):

```
MessageSid=SMxxxxxxxxxxxxxxxxxxxxxxxxxxxxx&
AccountSid=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxx&
From=whatsapp%3A%2B14155238886&
To=whatsapp%3A%2B15558675310&
Body=Hello%2C+I+need+help+with+my+order&
NumMedia=0&
ProfileName=John+Doe&
WaId=14155238886
```

**Request Fields**:
- `MessageSid` (string): Twilio message SID
- `AccountSid` (string): Twilio account SID
- `From` (string): Sender WhatsApp number (format: `whatsapp:+1234567890`)
- `To` (string): Recipient WhatsApp number
- `Body` (string): Message body text
- `NumMedia` (string): Number of media attachments (default: "0")
- `ProfileName` (string, optional): Sender's WhatsApp profile name
- `WaId` (string, optional): WhatsApp ID

**Response: 200 OK** (empty TwiML response):

```
(empty body)
```

**Response: 403 Forbidden** (invalid signature):

```json
{
  "error": "InvalidSignature",
  "message": "Twilio signature validation failed"
}
```

**Message Splitting**:

If AI response exceeds 1600 characters, it will be split into multiple WhatsApp messages:
- Part 1: "Your response here... (part 1/3)"
- Part 2: "...continued response... (part 2/3)"
- Part 3: "...final part (part 3/3)"

**Example cURL** (for testing, requires valid signature):

```bash
curl -X POST https://api.yourdomain.com/api/webhooks/whatsapp \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -H "X-Twilio-Signature: <computed-signature>" \
  -d "MessageSid=SMxxx&AccountSid=ACxxx&From=whatsapp:+14155238886&To=whatsapp:+15558675310&Body=Hello&NumMedia=0&ProfileName=John Doe"
```

---

#### GET /api/webhooks/whatsapp/health

Health check for WhatsApp webhook (for Twilio verification).

**Response: 200 OK**

```json
{
  "status": "healthy",
  "webhook": "whatsapp",
  "channel": "whatsapp",
  "timestamp": "2026-03-20T10:30:00Z"
}
```

---

### Ticket Status

#### GET /api/tickets/{ticket_id}/status

Get ticket status by ID.

**Path Parameters**:
- `ticket_id` (string, required): Ticket UUID

**Response: 200 OK**

```json
{
  "ticket_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "responded",
  "channel": "web",
  "customer_email": "john.doe@example.com",
  "customer_name": "John Doe",
  "created_at": "2026-03-20T10:30:00Z",
  "updated_at": "2026-03-20T10:35:00Z",
  "response": "Thank you for contacting us! To reset your password, please follow these steps...",
  "escalation_reason": null
}
```

**Response Fields**:
- `ticket_id` (string): Ticket identifier
- `status` (string): Current status (`pending`, `processing`, `responded`, `escalated`, `closed`)
- `channel` (string): Support channel (`web`, `email`, `whatsapp`)
- `customer_email` (string): Customer email address
- `customer_name` (string, nullable): Customer name
- `created_at` (string): Ticket creation time (ISO 8601)
- `updated_at` (string): Last update time (ISO 8601)
- `response` (string, nullable): Agent's response (if available)
- `escalation_reason` (string, nullable): Reason for escalation (if escalated)

**Response: 404 Not Found**

```json
{
  "error": "TicketNotFound",
  "message": "Ticket with ID 550e8400-e29b-41d4-a716-446655440000 not found"
}
```

**Example cURL**:

```bash
curl https://api.yourdomain.com/api/tickets/550e8400-e29b-41d4-a716-446655440000/status
```

---

#### GET /api/tickets

List all tickets for a customer.

**Query Parameters**:
- `email` (string, required): Customer email address
- `limit` (integer, optional): Max tickets to return (1-100, default: 10)

**Response: 200 OK**

```json
{
  "customer_email": "john.doe@example.com",
  "total_tickets": 3,
  "tickets": [
    {
      "ticket_id": "550e8400-e29b-41d4-a716-446655440000",
      "status": "responded",
      "channel": "web",
      "created_at": "2026-03-20T10:30:00Z",
      "updated_at": "2026-03-20T10:35:00Z",
      "original_message": "I need help resetting my password.",
      "last_response": "Thank you for contacting us! To reset your password..."
    },
    {
      "ticket_id": "660e8400-e29b-41d4-a716-446655440001",
      "status": "escalated",
      "channel": "whatsapp",
      "created_at": "2026-03-19T14:20:00Z",
      "updated_at": "2026-03-19T14:25:00Z",
      "original_message": "I want a refund for order #12345",
      "last_response": "I'm escalating your refund request to our support team..."
    },
    {
      "ticket_id": "770e8400-e29b-41d4-a716-446655440002",
      "status": "closed",
      "channel": "email",
      "created_at": "2026-03-18T09:15:00Z",
      "updated_at": "2026-03-18T09:20:00Z",
      "original_message": "How do I update my billing information?",
      "last_response": "To update your billing information, please go to..."
    }
  ]
}
```

**Response Fields**:
- `customer_email` (string): Customer email
- `total_tickets` (integer): Number of tickets returned
- `tickets` (array): List of ticket summaries

**Example cURL**:

```bash
curl "https://api.yourdomain.com/api/tickets?email=john.doe@example.com&limit=10"
```

---

## Data Models

### WebFormSubmission

```typescript
interface WebFormSubmission {
  name: string;          // 2-255 characters
  email: string;         // Valid email format
  message: string;       // 10-5000 characters
}
```

### TicketResponse

```typescript
interface TicketResponse {
  ticket_id: string;                  // UUID
  status: "resolved" | "escalated";
  message: string;                    // AI response
  estimated_response_time: string;
  created_at: string;                 // ISO 8601 timestamp
}
```

### TicketStatus

```typescript
type TicketStatus =
  | "pending"      // Waiting for agent processing
  | "processing"   // Agent is generating response
  | "responded"    // Agent responded successfully
  | "escalated"    // Escalated to human agent
  | "closed";      // Ticket closed

interface TicketStatusResponse {
  ticket_id: string;
  status: TicketStatus;
  channel: "web" | "email" | "whatsapp";
  customer_email: string;
  customer_name: string | null;
  created_at: string;              // ISO 8601
  updated_at: string;              // ISO 8601
  response: string | null;
  escalation_reason: string | null;
}
```

### HealthCheckResponse

```typescript
interface HealthCheckResponse {
  status: "healthy" | "unhealthy";
  version: string;
  timestamp: string;                 // ISO 8601
  database: string;
  ai_provider: string;
}
```

### ErrorResponse

```typescript
interface ErrorResponse {
  error: string;                     // Error type
  message: string;                   // Human-readable message
  detail?: Record<string, any>;      // Additional details
  request_id?: string;               // Request tracking ID
}
```

---

## Rate Limits

### Web Support Form
- **Limit**: 100 requests per minute per IP address
- **Response**: HTTP 429 with `Retry-After` header

### Webhooks
- **Gmail**: Limited by Google Pub/Sub (not rate limited on our end)
- **WhatsApp**: Limited by Twilio (not rate limited on our end)

### Ticket Queries
- **Limit**: 1000 requests per hour per email address
- **Response**: HTTP 429 with `Retry-After` header

**Rate Limit Headers**:

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1679308800
```

---

## Webhooks

### Setting Up Gmail Webhook

1. **Create Pub/Sub Topic** (Google Cloud Console):
   ```bash
   gcloud pubsub topics create gmail-notifications
   ```

2. **Create Push Subscription**:
   ```bash
   gcloud pubsub subscriptions create gmail-notifications-sub \
     --topic=gmail-notifications \
     --push-endpoint=https://api.yourdomain.com/api/webhooks/gmail
   ```

3. **Configure Gmail Watch**:
   ```bash
   # Use Gmail API to watch inbox
   POST https://www.googleapis.com/gmail/v1/users/me/watch
   {
     "topicName": "projects/YOUR_PROJECT/topics/gmail-notifications",
     "labelIds": ["INBOX"]
   }
   ```

4. **Verify Endpoint**: Visit `https://api.yourdomain.com/api/webhooks/gmail/health`

---

### Setting Up WhatsApp Webhook

1. **Get Twilio WhatsApp Number**: https://console.twilio.com/us1/develop/sms/try-it-out/whatsapp-learn

2. **Configure Webhook URL** (Twilio Console):
   - When a message comes in: `https://api.yourdomain.com/api/webhooks/whatsapp`
   - HTTP Method: POST

3. **Test Webhook**: Send "join [your-sandbox-word]" to your Twilio WhatsApp number

4. **Verify Endpoint**: Visit `https://api.yourdomain.com/api/webhooks/whatsapp/health`

**Webhook Signature Validation**:

Twilio signs requests with HMAC-SHA1. Our API automatically validates signatures using `X-Twilio-Signature` header.

To test locally with signature validation disabled:
```bash
export TWILIO_AUTH_TOKEN="test"  # Use test token to bypass validation
```

---

## Channel-Specific Formatting

The Digital FTE agent formats responses differently for each channel:

### Web Form
- **Style**: Semi-formal
- **Max Length**: 300 words
- **Format**: Markdown support, structured answers

### Gmail (Email)
- **Style**: Formal with greeting and signature
- **Max Length**: 500 words
- **Format**:
  ```
  Dear [Customer Name],

  [Response content]

  Best regards,
  Digital FTE Customer Success Agent
  ```

### WhatsApp
- **Style**: Concise and conversational
- **Preferred Length**: < 300 characters
- **Max Length**: 1600 characters per message (splits if longer)
- **Format**: No greeting, direct answer

---

## Testing

### Local Testing

```bash
# Start API
cd backend
uvicorn src.api.main:app --reload --port 8000

# Test web form
curl -X POST http://localhost:8000/api/support \
  -H "Content-Type: application/json" \
  -d '{"name":"Test User","email":"test@example.com","message":"Test message"}'

# Test health check
curl http://localhost:8000/health
```

### Webhook Testing with ngrok

```bash
# Install ngrok
brew install ngrok  # macOS
# or download from https://ngrok.com

# Start ngrok tunnel
ngrok http 8000

# Use ngrok URL for webhooks
# Example: https://abc123.ngrok.io/api/webhooks/whatsapp
```

---

## SDKs and Client Libraries

### JavaScript/TypeScript

```typescript
// Example: Submit web form
async function submitSupportRequest(data: {
  name: string;
  email: string;
  message: string;
}) {
  const response = await fetch('https://api.yourdomain.com/api/support', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${await response.text()}`);
  }

  return await response.json();
}

// Example: Get ticket status
async function getTicketStatus(ticketId: string) {
  const response = await fetch(
    `https://api.yourdomain.com/api/tickets/${ticketId}/status`
  );

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${await response.text()}`);
  }

  return await response.json();
}
```

### Python

```python
import requests

# Example: Submit web form
def submit_support_request(name: str, email: str, message: str):
    response = requests.post(
        'https://api.yourdomain.com/api/support',
        json={
            'name': name,
            'email': email,
            'message': message,
        }
    )
    response.raise_for_status()
    return response.json()

# Example: Get ticket status
def get_ticket_status(ticket_id: str):
    response = requests.get(
        f'https://api.yourdomain.com/api/tickets/{ticket_id}/status'
    )
    response.raise_for_status()
    return response.json()
```

---

## Support

- **API Issues**: Check docs/RUNBOOK.md for troubleshooting
- **Webhook Setup**: See docs/TWILIO_WHATSAPP_SETUP.md
- **Deployment**: See docs/DEPLOYMENT.md

---

**API Version**: 1.0.0
**Last Updated**: 2026-03-20
**Built with**: Groq AI (llama-3.3-70b-versatile), FastAPI, PostgreSQL 16
