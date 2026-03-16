# Digital FTE Customer Success Agent

**🤖 24/7 Autonomous Customer Support across Gmail, WhatsApp, and Web Form**

A production-grade Digital Full-Time Equivalent (FTE) that handles customer support requests autonomously using OpenAI Agents SDK, PostgreSQL as CRM, Kafka event streaming, and Kubernetes deployment. Replaces $75,000/year human FTE with < $1,000/year AI system operating 24/7 with > 99.9% uptime.

## 🎯 Project Overview

**Duration**: 48-72 development hours | **Team**: 1 student | **Difficulty**: Advanced

**Success Metrics**:
- ✅ Uptime > 99.9% during 24-hour continuous operation
- ✅ P95 latency < 3 seconds (processing)
- ✅ Escalation rate < 25%
- ✅ Cross-channel customer ID accuracy > 95%
- ✅ Zero message loss (Kafka at-least-once delivery)
- ✅ Cost per interaction < $0.10

## 📋 Table of Contents

- [Architecture](#architecture)
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Development Workflow](#development-workflow)
- [Testing](#testing)
- [Deployment](#deployment)
- [Documentation](#documentation)
- [License](#license)

## 🏗️ Architecture

```
┌─── CUSTOMER CHANNELS ────┬────── GMAIL ────┬──── WHATSAPP ────┬──── WEB FORM ────┐
│                          │                 │                  │                  │
│ Gmail API + Pub/Sub  ←────┤                │                  │                  │
│ Twilio WhatsApp API  ←────┼────────────────┤                  │                  │
│ React/Next.js Form   ←────┼────────────────┼──────────────────┤                  │
└──────────────────────────┴─────────────────┴──────────────────┴──────────────────┘
                                      ↓
┌────────────────── FASTAPI SERVICE (Min 3 replicas) ──────────────────────────────┐
│  /webhooks/gmail  │  /webhooks/whatsapp  │  /webhooks/web  │  /tickets/{id}/status │
└─────────────────────────────────────┬─────────────────────────────────────────────┘
                                      ↓ Publish to Kafka
┌─────────────────── KAFKA EVENT STREAMING (At-least-once delivery) ───────────────┐
│  fte.tickets.incoming (unified) │ fte.tickets.{gmail,whatsapp,web} (analytics)  │
└─────────────────────────────────┬──────────────────────────────────────────────────┘
                                  ↓ Consume
┌─────────────── MESSAGE PROCESSOR WORKERS (Min 3 replicas, stateless) ────────────┐
│  OpenAI Agents SDK → create_ticket → get_customer_history → search_knowledge_base│
│  → send_response (channel-specific formatting) OR escalate_to_human             │
└───────────┬─────────────────────────┬────────────────────────────────────────────┘
            ↓                         ↓
┌───── POSTGRESQL 16 (CRM) ──────┐   ┌─── CHANNEL RESPONSE DELIVERY ────────────┐
│ customers, customer_identifiers│   │ Gmail API | Twilio API | Web + Email    │
│ conversations, messages, tickets│   └──────────────────────────────────────────┘
│ knowledge_base (pgvector)      │
│ channel_configs, agent_metrics │
└────────────────────────────────┘
```

## ✨ Features

### Multi-Channel Support
- **Gmail (Email)**: Formal, detailed responses (max 500 words) with greeting/signature
- **WhatsApp (Messaging)**: Concise, conversational (max 300 chars preferred)
- **Web Form (Website)**: MANDATORY React/Next.js component with validation and status tracking

### Cross-Channel Customer Continuity
- Email as primary customer identifier
- Phone number linking via `customer_identifiers` table
- > 95% accuracy in identifying same customer across channels
- Complete conversation history preserved regardless of channel

### AI Agent Capabilities
- **Autonomous**: Handles 75%+ of customer questions without human intervention
- **Knowledge Base Search**: pgvector semantic similarity for product documentation
- **Intelligent Escalation**: Pricing, refunds, legal, sentiment < 0.3 → human agent
- **24/7 Availability**: No downtime, vacations, sick leave required

### Production-Grade Infrastructure
- **Kubernetes**: HorizontalPodAutoscaler (3-20 API pods, 3-30 workers)
- **Kafka**: Distributed event streaming with at-least-once delivery guarantee
- **PostgreSQL 16**: Complete CRM system with pgvector extension (no external CRM needed)
- **Chaos Resilience**: Survives random pod kills every 2 hours

## 🔧 Prerequisites

### Required Software
- **Python 3.11+** with pip
- **Node.js 18+** with npm
- **Docker & Docker Compose** for local development
- **Kubernetes cluster** (Minikube for local or GKE/EKS/AKS for cloud)
- **kubectl** configured with cluster access

### Required API Accounts
- **OpenAI API** with GPT-4o access (for Agents SDK)
- **Google Cloud** project with Gmail API enabled
- **Twilio** account with WhatsApp sandbox or approved number
- **Confluent Cloud** (recommended) or self-hosted Kafka cluster

### Required Environment Variables
Copy `.env.example` to `.env` and fill in:
- `OPENAI_API_KEY`: Your OpenAI API key
- `DATABASE_URL`: PostgreSQL connection string
- `KAFKA_BROKER`: Kafka broker address
- `GMAIL_CREDENTIALS_FILE`: Path to Gmail OAuth2 credentials
- `TWILIO_ACCOUNT_SID` & `TWILIO_AUTH_TOKEN`: Twilio credentials

## 🚀 Quick Start

### 1. Clone and Setup

```bash
# Clone repository
git clone <repository-url>
cd digital-fte

# Create virtual environment (Python)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python dependencies
pip install -r backend/requirements.txt

# Install Node.js dependencies
cd frontend
npm install
cd ..

# Copy environment template
cp .env.example .env
# Edit .env with your actual credentials
```

### 2. Start Local Development Environment

```bash
# Start PostgreSQL and Kafka with Docker Compose
docker-compose up -d postgres kafka zookeeper

# Run database migrations
cd backend
python -m src.database.migrations.run

# Seed knowledge base with sample data
python -m src.database.seed_knowledge_base

# Generate pgvector embeddings
python -m src.database.generate_embeddings
```

### 3. Run Backend & Frontend

```bash
# Terminal 1: Start FastAPI backend
cd backend
uvicorn src.api.main:app --reload --port 8000

# Terminal 2: Start message processor workers
cd backend
python -m src.workers.message_processor

# Terminal 3: Start Next.js frontend
cd frontend
npm run dev
```

### 4. Access Web Support Form

Visit `http://localhost:3000` to see the Web Support Form.

Submit a test question and check your email for the Digital FTE's response!

## 🛠️ Development Workflow

This project follows **SpecKit Plus methodology** (Constitution → Specify → Plan → Tasks → Implement):

1. **Constitution** (✅ Complete): `.specify/memory/constitution.md`
2. **Specification** (✅ Complete): `specs/digital-fte/spec.md`
3. **Implementation Plan** (✅ Complete): `specs/digital-fte/plan.md`
4. **Actionable Tasks** (✅ Complete): `specs/digital-fte/tasks.md` (167 tasks)
5. **Implementation**: Currently in Phase 1 (Setup)

### Two-Stage Development Process

#### Stage 1: Incubation (Hours 1-16) - Claude Code Exploration
- Build MCP server prototype (`incubation/mcp_server.py`)
- Define agent tools and discover edge cases
- Document findings in `specs/digital-fte/discovery-log.md`

#### Stage 2: Specialization (Hours 17-40) - Production Build
- Convert MCP tools to OpenAI Agents SDK with Pydantic validation
- Build all three channel integrations
- Deploy to Kubernetes with autoscaling

## 🧪 Testing

### Unit Tests
```bash
cd backend
pytest tests/unit/ --cov=src --cov-report=html
# Coverage report: htmlcov/index.html
```

### Integration Tests (E2E per channel)
```bash
pytest tests/integration/test_web_flow.py
pytest tests/integration/test_gmail_flow.py
pytest tests/integration/test_whatsapp_flow.py
pytest tests/integration/test_cross_channel.py
```

### Chaos Tests
```bash
# Kill random pod every 2 hours, verify zero message loss
pytest tests/chaos/test_pod_kills.py --duration=6h
```

### Load Tests
```bash
cd backend/tests/load
k6 run k6_load_test.js --vus 100 --duration 10m
```

### 24-Hour Continuous Operation Test (FINAL CHALLENGE)
```bash
# Start 24-hour test with chaos engineering
cd backend/tests/24h
python load_generator.py &  # 100+ web, 50+ email, 50+ WhatsApp
python chaos_runner.py &    # Pod kills every 2h
python metrics_collector.py  # Monitor uptime, latency, escalation rate

# After 24 hours, verify:
# - Uptime > 99.9%
# - P95 latency < 3s
# - Escalation rate < 25%
# - Zero message loss
# - Cross-channel ID accuracy > 95%
```

## 🚢 Deployment

### Deploy to Kubernetes

```bash
# Create namespace and secrets
kubectl create namespace digital-fte
kubectl create secret generic digital-fte-secrets \
  --from-literal=database-password=<password> \
  --from-literal=openai-api-key=<key> \
  --from-file=gmail-credentials=credentials/gmail_credentials.json \
  --from-literal=twilio-auth-token=<token>

# Deploy all services
kubectl apply -f k8s/

# Verify deployment
kubectl get pods -n digital-fte
kubectl get hpa -n digital-fte  # Check autoscaling

# Access Web Form via LoadBalancer
kubectl get svc -n digital-fte digital-fte-api
```

### Monitor Autoscaling

```bash
# Watch HPA scale API and workers
kubectl get hpa -n digital-fte --watch

# Generate load to trigger scaling
k6 run backend/tests/load/k6_load_test.js --vus 200 --duration 30m
```

## 📚 Documentation

- **Specification**: `specs/digital-fte/spec.md` - Complete feature requirements
- **Implementation Plan**: `specs/digital-fte/plan.md` - Architecture and design
- **Tasks**: `specs/digital-fte/tasks.md` - 167 actionable tasks with dependencies
- **Constitution**: `.specify/memory/constitution.md` - Project principles and standards
- **API Documentation**: `docs/API.md` - All endpoints and schemas
- **Agent Tools**: `docs/AGENT_TOOLS.md` - OpenAI Agents SDK tools
- **Deployment Guide**: `docs/DEPLOYMENT.md` - Kubernetes setup
- **Runbook**: `docs/RUNBOOK.md` - Incident response procedures

## 🎓 Learning Resources

- [OpenAI Agents SDK Documentation](https://platform.openai.com/docs/guides/agents)
- [pgvector Extension](https://github.com/pgvector/pgvector)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Kafka Event Streaming](https://kafka.apache.org/documentation/)
- [Kubernetes Autoscaling](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/)

## 📊 Project Status

- ✅ **Constitution** complete
- ✅ **Specification** complete (5 user stories, 27 functional requirements)
- ✅ **Implementation Plan** complete (database schema, agent tools, architecture)
- ✅ **Tasks** complete (167 tasks across 11 phases)
- 🚧 **Phase 1: Setup** in progress (directory structure created)
- ⏳ **Phase 2: Foundational** (next - database, Kafka, models)
- ⏳ **Phase 3-6: User Stories** (Web Form, Gmail, WhatsApp, Cross-Channel)
- ⏳ **Phase 7: OpenAI Agents SDK** (production implementation)
- ⏳ **Phase 8: Kubernetes Deployment**
- ⏳ **Phase 9: Testing**
- ⏳ **Phase 10: 24-Hour Continuous Operation Test**

## 📄 License

This project is developed as part of "The CRM Digital FTE Factory" hackathon challenge.

---

**Built with** ❤️ **using Claude Code, OpenAI Agents SDK, and SpecKit Plus methodology**
