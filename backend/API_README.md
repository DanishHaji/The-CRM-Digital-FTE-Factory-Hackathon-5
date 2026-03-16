# Digital FTE API - FastAPI Service

Multi-channel customer support API with AI-powered agent.

## Quick Start

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Set Up Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your credentials
nano .env

# REQUIRED: Set your OpenAI API key
OPENAI_API_KEY=sk-your-key-here
```

### 3. Start Dependencies

```bash
# Start PostgreSQL and Kafka using Docker Compose
docker-compose up -d postgres kafka zookeeper
```

### 4. Initialize Database

```bash
# Create schema
psql $DATABASE_URL < src/database/schema.sql

# Seed knowledge base
python -m src.database.seed_knowledge_base

# Generate embeddings
python -m src.database.generate_embeddings
```

### 5. Run API Server

```bash
# Development mode (auto-reload)
python run_api.py --reload

# Production mode (4 workers)
python run_api.py --workers 4

# Or use uvicorn directly
cd src
uvicorn api.main:app --reload
```

### 6. Test the API

```bash
# Check health
curl http://localhost:8000/api/health

# Submit web form
curl -X POST http://localhost:8000/api/webhooks/web \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john@example.com",
    "message": "How do I reset my password?"
  }'

# Check ticket status
curl http://localhost:8000/api/tickets/{ticket_id}/status
```

## API Documentation

Once the server is running, visit:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## Architecture

### Components

```
backend/
├── src/
│   ├── api/                    # FastAPI application
│   │   ├── main.py             # Main app with lifespan, middleware
│   │   ├── routes/             # Endpoint handlers
│   │   │   ├── web.py          # Web form webhook
│   │   │   ├── gmail.py        # Gmail Pub/Sub webhook
│   │   │   ├── whatsapp.py     # WhatsApp Twilio webhook
│   │   │   ├── tickets.py      # Ticket status queries
│   │   │   └── health.py       # Health checks
│   │   ├── models/             # Pydantic request/response models
│   │   │   ├── requests.py     # Input validation
│   │   │   └── responses.py    # Output schemas
│   │   └── middleware/         # Middleware components
│   │       ├── logging.py      # Request logging with context
│   │       └── error_handler.py # Global error handling
│   ├── agent/                  # OpenAI Agents SDK
│   │   ├── customer_success_agent.py  # Main agent
│   │   ├── tools.py            # 5 production tools
│   │   └── prompts.py          # Channel-specific prompts
│   ├── database/               # PostgreSQL
│   │   ├── schema.sql          # Database schema
│   │   ├── connection.py       # Async connection pool
│   │   └── seed_knowledge_base.py
│   ├── kafka/                  # Message streaming
│   │   ├── producer.py         # Async producer
│   │   ├── consumer.py         # Async consumer
│   │   └── topics.py           # Topic definitions
│   ├── models/                 # Pydantic data models
│   └── utils/                  # Utilities
│       ├── config.py           # Pydantic Settings
│       ├── logger.py           # Structured logging
│       └── validators.py       # Input validation
└── run_api.py                  # API server runner
```

### Data Flow

1. **Request arrives** at webhook endpoint (web, gmail, whatsapp)
2. **Validation** happens automatically via Pydantic models
3. **Message published** to Kafka `fte.tickets.incoming` topic
4. **Response returned** to client (200 OK for webhooks, ticket_id for web)
5. **Worker consumes** message from Kafka (separate process)
6. **Agent processes** request using OpenAI Agents SDK
7. **Response sent** to customer via appropriate channel
8. **Ticket updated** in PostgreSQL with status and response

## Endpoints

### Web Form

```http
POST /api/webhooks/web
Content-Type: application/json

{
  "name": "John Doe",
  "email": "john@example.com",
  "message": "I need help with my order #12345"
}

Response: 201 Created
{
  "ticket_id": "550e8400-e29b-41d4-a716-446655440000",
  "conversation_id": "...",
  "customer_id": "...",
  "status": "pending",
  "channel": "web",
  "message": "Support ticket created successfully...",
  "created_at": "2026-03-16T10:30:00Z"
}
```

### Gmail Webhook

```http
POST /api/webhooks/gmail
Content-Type: application/json

{
  "message": {
    "data": "eyJlbWFpbElkIjogIjE4YzM1...",
    "messageId": "2070443601311540",
    "publishTime": "2021-02-26T19:13:55.749Z"
  },
  "subscription": "projects/myproject/subscriptions/gmail-sub"
}

Response: 200 OK
{
  "status": "processing",
  "message": "Gmail notification received and queued",
  "ticket_id": "..."
}
```

### WhatsApp Webhook

```http
POST /api/webhooks/whatsapp
Content-Type: application/x-www-form-urlencoded

MessageSid=SM1234...
From=whatsapp:+14155238886
To=whatsapp:+15558675310
Body=Hello, I need help with my order

Response: 200 OK
{
  "status": "processing",
  "message": "WhatsApp message received and queued",
  "ticket_id": "..."
}
```

### Ticket Status

```http
GET /api/tickets/{ticket_id}/status

Response: 200 OK
{
  "ticket_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "responded",
  "channel": "web",
  "customer_email": "john@example.com",
  "customer_name": "John Doe",
  "created_at": "2026-03-16T10:30:00Z",
  "updated_at": "2026-03-16T10:35:00Z",
  "response": "Thank you for contacting us! To reset your password...",
  "escalation_reason": null
}
```

### Health Check

```http
GET /api/health

Response: 200 OK
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2026-03-16T10:30:00Z",
  "database": "connected",
  "kafka": "connected"
}
```

## Configuration

All configuration is via environment variables (see `.env.example`).

### Required Settings

- `OPENAI_API_KEY` - Your OpenAI API key
- `DATABASE_URL` - PostgreSQL connection string
- `KAFKA_BROKER` - Kafka broker address

### Optional Settings

- `API_HOST` - Bind host (default: 0.0.0.0)
- `API_PORT` - Bind port (default: 8000)
- `API_WORKERS` - Number of worker processes (default: 4)
- `CORS_ORIGINS` - Allowed CORS origins (comma-separated)
- `LOG_LEVEL` - Logging level (INFO, DEBUG, WARNING, ERROR)

## Monitoring

### Structured Logs

All logs are in JSON format with context:

```json
{
  "event": "request_completed",
  "request_id": "550e8400-...",
  "method": "POST",
  "path": "/api/webhooks/web",
  "status_code": 201,
  "process_time_seconds": 0.0234,
  "timestamp": "2026-03-16T10:30:00Z"
}
```

### Metrics

The API exposes metrics via logs:

- Request count by endpoint
- Response times (p50, p95, p99)
- Error rates
- Ticket creation rate
- Agent processing time

### Health Checks

- `/api/health` - Overall health (database + Kafka)
- `/api/health/liveness` - Kubernetes liveness probe
- `/api/health/readiness` - Kubernetes readiness probe

## Security

### Request Validation

- All inputs validated with Pydantic
- Email format validation (RFC 5322)
- XSS prevention (input sanitization)
- SQL injection prevention (parameterized queries)

### Webhook Signatures

- **Gmail**: Verified by Google Cloud Pub/Sub
- **WhatsApp**: Twilio signature validation (X-Twilio-Signature)

### CORS

Configure allowed origins in `.env`:

```bash
CORS_ORIGINS=http://localhost:3000,https://yourcompany.com
```

### API Keys

For production, set a strong API key:

```bash
API_KEY=your-strong-random-api-key-here
```

## Error Handling

All errors return consistent format:

```json
{
  "error": "ValidationError",
  "message": "Request validation failed",
  "detail": [
    {
      "field": "email",
      "message": "Invalid email format",
      "type": "value_error"
    }
  ],
  "request_id": "550e8400-..."
}
```

### Error Codes

- `400` - Bad Request (invalid payload)
- `403` - Forbidden (invalid signature)
- `404` - Not Found (ticket not found)
- `422` - Unprocessable Entity (validation error)
- `500` - Internal Server Error

## Development

### Running Tests

```bash
# Unit tests
pytest tests/

# With coverage
pytest --cov=src tests/

# Specific test file
pytest tests/test_api/test_web.py -v
```

### Adding a New Endpoint

1. Create route handler in `src/api/routes/your_route.py`
2. Define request/response models in `src/api/models/`
3. Register router in `src/api/main.py`
4. Add tests in `tests/test_api/test_your_route.py`

### Hot Reload

Use `--reload` flag for development:

```bash
python run_api.py --reload
```

## Deployment

### Docker

```bash
# Build image
docker build -t digital-fte-api .

# Run container
docker run -p 8000:8000 --env-file .env digital-fte-api
```

### Kubernetes

See `k8s/api-deployment.yaml` for deployment manifests.

```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/api-configmap.yaml
kubectl apply -f k8s/api-secret.yaml
kubectl apply -f k8s/api-deployment.yaml
kubectl apply -f k8s/api-service.yaml
```

### Production Checklist

- [ ] Set `ENVIRONMENT=production`
- [ ] Use strong `API_KEY`
- [ ] Configure SSL/TLS certificates
- [ ] Set proper `CORS_ORIGINS`
- [ ] Use managed PostgreSQL (AWS RDS, etc.)
- [ ] Use managed Kafka (Confluent Cloud, etc.)
- [ ] Enable authentication middleware
- [ ] Set up monitoring/alerting
- [ ] Configure log aggregation (ELK, Datadog, etc.)
- [ ] Set resource limits in Kubernetes
- [ ] Configure HorizontalPodAutoscaler
- [ ] Enable health checks

## Troubleshooting

### API won't start

```bash
# Check database connection
psql $DATABASE_URL -c "SELECT 1"

# Check Kafka broker
kafkacat -b $KAFKA_BROKER -L
```

### Webhook not receiving messages

- **Gmail**: Check Pub/Sub subscription in Google Cloud Console
- **WhatsApp**: Verify webhook URL in Twilio Console
- Check firewall rules and network connectivity

### Database errors

```bash
# Reset database
psql $DATABASE_URL < src/database/schema.sql

# Check connections
psql $DATABASE_URL -c "SELECT * FROM pg_stat_activity"
```

## Support

For issues, see:

- API documentation: http://localhost:8000/docs
- Project README: `../README.md`
- Constitution: `../.specify/memory/constitution.md`
- Spec: `../specs/digital-fte/spec.md`

---

**Built with FastAPI, OpenAI Agents SDK, PostgreSQL, and Kafka**

**Status**: Production Ready
