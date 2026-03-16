# Implementation Plan: Digital FTE Customer Success Agent

**Branch**: `master` | **Date**: 2026-03-14 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/digital-fte/spec.md`

## Summary

Build a production-grade, 24/7 autonomous Customer Success Agent that handles support requests across three channels (Gmail, WhatsApp, Web Form) using OpenAI Agents SDK, PostgreSQL as CRM, Kafka event streaming, and Kubernetes deployment. The system must achieve > 99.9% uptime, < 3s P95 latency, < 25% escalation rate, and operate at < $1,000/year compared to $75,000/year human FTE.

**Technical Approach**:
- **Stage 1 (Incubation)**: Claude Code exploration with MCP server to define tools, discover edge cases, crystallize requirements
- **Stage 2 (Specialization)**: OpenAI Agents SDK production implementation with Pydantic validation, Kafka event streaming, multi-channel handlers
- **Stage 3 (Integration)**: E2E testing, chaos engineering, 24-hour continuous operation validation

## Technical Context

**Language/Version**: Python 3.11+ (backend/agent), Node.js 18+ (Web Form frontend)
**Primary Dependencies**:
- OpenAI Agents SDK (GPT-4o)
- FastAPI 0.104+ (async/await)
- PostgreSQL 16 (pgvector extension)
- Apache Kafka (Confluent Cloud or self-hosted)
- Pydantic 2.5+ (validation)
- React 18 + Next.js 14 (Web Form)
- Google Gmail API, Twilio WhatsApp API

**Storage**: PostgreSQL 16 with pgvector extension (serves as complete CRM system)
**Testing**: pytest (backend), Jest + React Testing Library (frontend), K6 (load testing), chaos-mesh (chaos engineering)
**Target Platform**: Kubernetes (Minikube local or GKE/EKS/AKS cloud) with Linux containers
**Project Type**: Web application with backend API, agent workers, and frontend Web Form component
**Performance Goals**:
- P95 latency < 3 seconds (processing)
- Total delivery time < 30 seconds
- Uptime > 99.9%
- Throughput: 100+ concurrent requests
**Constraints**:
- Zero message loss (Kafka at-least-once delivery)
- Cross-channel ID accuracy > 95%
- Escalation rate < 25%
- Cost per interaction < $0.10
**Scale/Scope**:
- 24-hour test: 100+ web submissions, 50+ emails, 50+ WhatsApp messages
- 10+ cross-channel customers
- Single student, 48-72 development hours

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

✅ **Customer Experience First**: All three channels implemented with channel-appropriate formatting (email: formal/detailed, WhatsApp: concise/conversational, Web: semi-formal)

✅ **Reliability & Operational Excellence**: Min 3 replicas for API/workers, HorizontalPodAutoscaler, Kafka distributed queue, PostgreSQL replication

✅ **Data Integrity & Privacy**: Email as primary identifier, customer_identifiers table for cross-channel linking, complete audit trail in messages table

✅ **Multi-Channel Architecture (NON-NEGOTIABLE)**: Unified `fte.tickets.incoming` Kafka topic, three channels required (Gmail, WhatsApp, Web Form)

✅ **PostgreSQL as CRM (NO EXTERNAL CRM)**: Database schema IS the CRM - customers, customer_identifiers, conversations, messages, tickets, knowledge_base tables

✅ **AI Agent Behavior Standards**: Hard constraints enforced (never discuss pricing/refunds), required workflow order (create_ticket → get_customer_history → search_knowledge_base → send_response)

✅ **Development Workflow: Incubation → Specialization**: Stage 1 (Claude Code MCP), Stage 2 (OpenAI Agents SDK production), Stage 3 (Integration testing)

✅ **Testing & Quality Gates**: Unit tests (> 80% coverage), integration tests (per channel), chaos tests (pod kills every 2h), 24-hour continuous operation test

## Project Structure

### Documentation (this feature)

```text
specs/digital-fte/
├── spec.md              # Feature specification (COMPLETED)
├── plan.md              # This file - implementation plan (IN PROGRESS)
├── tasks.md             # Actionable tasks with dependencies (NEXT)
├── research.md          # Phase 0 discovery findings (to be created)
├── data-model.md        # Database schema and entity relationships (included below)
├── contracts/           # API contracts and tool schemas
│   ├── agent-tools.md   # OpenAI Agents SDK tool definitions
│   ├── api-endpoints.md # FastAPI endpoint specifications
│   └── kafka-topics.md  # Event schema definitions
└── discovery-log.md     # Incubation phase findings (Stage 1 output)
```

### Source Code (repository root)

```text
# Web application structure (backend + agent workers + frontend)
backend/
├── src/
│   ├── agent/
│   │   ├── customer_success_agent.py    # OpenAI Agents SDK implementation
│   │   ├── tools.py                      # Agent tools (@function_tool decorators)
│   │   └── prompts.py                    # System prompts and templates
│   ├── models/
│   │   ├── customer.py                   # Pydantic models for customers
│   │   ├── conversation.py               # Pydantic models for conversations
│   │   ├── message.py                    # Pydantic models for messages
│   │   ├── ticket.py                     # Pydantic models for tickets
│   │   └── knowledge_base.py             # Pydantic models for KB entries
│   ├── channels/
│   │   ├── gmail_handler.py              # Gmail API + Pub/Sub integration
│   │   ├── whatsapp_handler.py           # Twilio WhatsApp integration
│   │   └── web_handler.py                # Web Form submission handler
│   ├── workers/
│   │   ├── message_processor.py          # Unified Kafka consumer
│   │   └── response_sender.py            # Channel-specific response delivery
│   ├── api/
│   │   ├── main.py                       # FastAPI app entry point
│   │   ├── routes/
│   │   │   ├── gmail.py                  # Gmail webhook endpoint
│   │   │   ├── whatsapp.py               # Twilio webhook endpoint
│   │   │   └── web.py                    # Web Form submission endpoint
│   │   └── middleware/
│   │       ├── auth.py                   # API authentication
│   │       └── logging.py                # Structured logging
│   ├── database/
│   │   ├── schema.sql                    # PostgreSQL schema with pgvector
│   │   ├── migrations/                   # Database migration scripts
│   │   └── connection.py                 # Connection pool management
│   ├── kafka/
│   │   ├── producer.py                   # Kafka producer client
│   │   ├── consumer.py                   # Kafka consumer client
│   │   └── topics.py                     # Topic definitions
│   └── utils/
│       ├── config.py                     # Environment config management
│       ├── logger.py                     # Structured logging setup
│       └── validators.py                 # Custom Pydantic validators
├── tests/
│   ├── unit/
│   │   ├── test_tools.py                 # Agent tool unit tests
│   │   ├── test_channels.py              # Channel handler unit tests
│   │   └── test_models.py                # Pydantic model validation tests
│   ├── integration/
│   │   ├── test_gmail_flow.py            # E2E Gmail flow test
│   │   ├── test_whatsapp_flow.py         # E2E WhatsApp flow test
│   │   ├── test_web_flow.py              # E2E Web Form flow test
│   │   └── test_cross_channel.py         # Cross-channel customer ID test
│   ├── chaos/
│   │   └── test_pod_kills.py             # Chaos engineering tests
│   └── load/
│       └── k6_load_test.js               # K6 load testing script
├── Dockerfile                             # Multi-stage Docker build
├── requirements.txt                       # Python dependencies
└── pyproject.toml                         # Python project config

frontend/
├── src/
│   ├── components/
│   │   ├── SupportForm.jsx               # MANDATORY Web Support Form (REQUIRED)
│   │   ├── FormValidation.js             # Client-side validation logic
│   │   └── StatusDisplay.jsx             # Ticket status component
│   ├── pages/
│   │   ├── index.jsx                     # Support page entry point
│   │   └── api/
│   │       └── submit.js                 # Next.js API route (proxy to backend)
│   ├── services/
│   │   └── api.js                        # Backend API client
│   └── styles/
│       └── support-form.css              # Form styling
├── tests/
│   ├── SupportForm.test.jsx              # React component tests
│   └── validation.test.js                # Validation logic tests
├── package.json                           # Node.js dependencies
└── next.config.js                         # Next.js configuration

k8s/
├── namespace.yaml                         # Kubernetes namespace
├── configmap.yaml                         # Environment configuration
├── secrets.yaml                           # Secrets (Gmail, Twilio, OpenAI keys)
├── api-deployment.yaml                    # FastAPI deployment (min 3 replicas)
├── worker-deployment.yaml                 # Message processor deployment (min 3)
├── api-service.yaml                       # API service (LoadBalancer)
├── api-hpa.yaml                           # API HorizontalPodAutoscaler (3-20)
├── worker-hpa.yaml                        # Worker HorizontalPodAutoscaler (3-30)
├── postgres-statefulset.yaml              # PostgreSQL StatefulSet
├── postgres-service.yaml                  # PostgreSQL service
├── kafka-deployment.yaml                  # Kafka deployment (if self-hosted)
└── ingress.yaml                           # Ingress for Web Form

incubation/
├── mcp_server.py                          # Model Context Protocol server (Stage 1)
├── tools/                                 # Initial tool definitions
│   ├── create_ticket.py
│   ├── get_customer_history.py
│   ├── search_knowledge_base.py
│   ├── send_response.py
│   └── escalate_to_human.py
└── test_scenarios/                        # Edge case discovery tests
    ├── pricing_questions.txt
    ├── refund_requests.txt
    ├── cross_channel_scenarios.txt
    └── angry_customers.txt

docker-compose.yml                         # Local development environment
README.md                                  # Project overview and setup
.env.example                               # Environment variables template
```

**Structure Decision**: Web application structure chosen due to separate concerns:
1. **Backend** (Python FastAPI): API layer, channel handlers, Kafka producers
2. **Agent Workers** (Python OpenAI SDK): Stateless message processors consuming from Kafka
3. **Frontend** (React/Next.js): MANDATORY Web Support Form component (REQUIRED deliverable)
4. **Incubation** (Temporary): Stage 1 MCP server for tool discovery, deleted after transition to production

## Phase 0: Research & Discovery (Incubation Stage 1)

### Objective
Use Claude Code as Agent Factory to explore the problem space, define agent capabilities, discover edge cases, and crystallize requirements through iterative prototyping with Model Context Protocol (MCP) server.

### Research Questions
1. **What are the minimum tool capabilities needed for autonomous customer support?**
   - create_ticket: Create support ticket with channel metadata
   - get_customer_history: Retrieve cross-channel conversation history
   - search_knowledge_base: Query product documentation using pgvector
   - send_response: Format and deliver response to appropriate channel
   - escalate_to_human: Escalate complex/sensitive issues with context

2. **What edge cases emerge in multi-channel customer support?**
   - Customer asks pricing question → Must escalate (hard constraint)
   - Customer uses profanity or mentions "lawyer" → Escalation trigger
   - Customer contacts via email then WhatsApp → Must link identities
   - WhatsApp response exceeds 1600 chars → Must split message
   - Knowledge base search returns no results → Escalate after 2 attempts
   - Duplicate message received (same channel_message_id) → Idempotent skip
   - Gmail API quota exceeded → Exponential backoff with Kafka retry

3. **How do channel-specific constraints affect agent behavior?**
   - Email: Formal tone, detailed (max 500 words), greeting + signature required
   - WhatsApp: Concise (< 300 chars preferred), conversational, no formal greeting
   - Web Form: Semi-formal, helpful, balanced (max 300 words), confirmation email sent
   - Response generation: Single tool call, channel parameter determines formatting

4. **What prompt engineering patterns improve response quality?**
   - System prompt includes channel context: "You are responding via {channel}"
   - Tool calling order enforced: create_ticket FIRST, send_response LAST
   - Escalation decision logic: "If uncertain after 2 KB searches, escalate"
   - Cross-channel continuity: "Check customer history across ALL channels before responding"

### Deliverables
- `incubation/mcp_server.py`: Working MCP server with 5 tools
- `specs/digital-fte/discovery-log.md`: Edge cases, prompt patterns, tool schemas documented
- `specs/digital-fte/spec.md`: Crystallized specification (COMPLETED)
- `incubation/test_scenarios/`: 20+ edge case test inputs per channel

### Success Criteria
- MCP server handles sample questions from all three channels with correct tool calling order
- Edge cases documented with expected agent behavior
- Tool input/output schemas defined (ready for Pydantic conversion in Stage 2)

## Phase 1: Data Model & Architecture Design

### Database Schema (PostgreSQL 16 with pgvector)

```sql
-- Enable pgvector extension for semantic search
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Unified customer records across all channels
CREATE TABLE customers (
    customer_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,  -- Primary identifier
    name VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'  -- Channel-specific data
);

-- Cross-channel identity linking (email, phone, whatsapp_id)
CREATE TABLE customer_identifiers (
    identifier_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id UUID REFERENCES customers(customer_id) ON DELETE CASCADE,
    identifier_type VARCHAR(50) NOT NULL,  -- 'email', 'phone', 'whatsapp_id'
    identifier_value VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(identifier_type, identifier_value)
);

-- Conversation sessions with initial_channel tracking
CREATE TABLE conversations (
    conversation_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id UUID REFERENCES customers(customer_id) ON DELETE CASCADE,
    initial_channel VARCHAR(50) NOT NULL,  -- 'email', 'whatsapp', 'web'
    status VARCHAR(50) DEFAULT 'open',  -- 'open', 'resolved', 'escalated'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- All messages with channel, direction, role tracking
CREATE TABLE messages (
    message_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID REFERENCES conversations(conversation_id) ON DELETE CASCADE,
    channel VARCHAR(50) NOT NULL,  -- 'email', 'whatsapp', 'web'
    direction VARCHAR(50) NOT NULL,  -- 'inbound', 'outbound'
    role VARCHAR(50) NOT NULL,  -- 'user', 'assistant'
    content TEXT NOT NULL,
    channel_message_id VARCHAR(255),  -- Gmail message_id, Twilio SID, web submission_id
    metadata JSONB DEFAULT '{}',  -- Channel-specific data (headers, sender, etc.)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(channel, channel_message_id)  -- Prevent duplicate processing
);

-- Support tickets with source_channel
CREATE TABLE tickets (
    ticket_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID REFERENCES conversations(conversation_id) ON DELETE CASCADE,
    source_channel VARCHAR(50) NOT NULL,  -- 'email', 'whatsapp', 'web'
    priority VARCHAR(50) DEFAULT 'medium',  -- 'low', 'medium', 'high', 'urgent'
    status VARCHAR(50) DEFAULT 'pending',  -- 'pending', 'processing', 'responded', 'escalated'
    assigned_to UUID,  -- NULL for Digital FTE, user_id for human escalation
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP
);

-- Product documentation with pgvector embeddings for semantic search
CREATE TABLE knowledge_base (
    entry_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    embedding VECTOR(1536),  -- OpenAI text-embedding-3-small dimension
    category VARCHAR(100),
    source_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for fast vector similarity search
CREATE INDEX ON knowledge_base USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Per-channel configuration
CREATE TABLE channel_configs (
    config_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    channel_name VARCHAR(50) UNIQUE NOT NULL,  -- 'email', 'whatsapp', 'web'
    enabled BOOLEAN DEFAULT true,
    config_json JSONB NOT NULL,  -- API keys, formatting rules, rate limits
    max_response_length INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Performance tracking by channel
CREATE TABLE agent_metrics (
    metric_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    channel VARCHAR(50) NOT NULL,
    ticket_id UUID REFERENCES tickets(ticket_id) ON DELETE CASCADE,
    response_time_ms INT NOT NULL,
    escalation BOOLEAN DEFAULT false,
    sentiment_score FLOAT,  -- -1.0 to 1.0
    customer_satisfaction INT,  -- 1-5 rating (optional)
    tool_calls JSONB,  -- Array of tool calls with inputs/outputs
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_customers_email ON customers(email);
CREATE INDEX idx_customer_identifiers_customer_id ON customer_identifiers(customer_id);
CREATE INDEX idx_conversations_customer_id ON conversations(customer_id);
CREATE INDEX idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX idx_messages_channel_message_id ON messages(channel, channel_message_id);
CREATE INDEX idx_tickets_conversation_id ON tickets(conversation_id);
CREATE INDEX idx_tickets_status ON tickets(status);
CREATE INDEX idx_agent_metrics_channel ON agent_metrics(channel);
CREATE INDEX idx_agent_metrics_created_at ON agent_metrics(created_at);
```

### Agent Tools (OpenAI Agents SDK @function_tool)

```python
# backend/src/agent/tools.py
from openai import OpenAI
from pydantic import BaseModel, Field
from typing import Literal
import uuid

class CreateTicketInput(BaseModel):
    """Input schema for create_ticket tool"""
    customer_email: str = Field(..., description="Customer's email address (primary identifier)")
    customer_name: str = Field(..., description="Customer's name")
    message: str = Field(..., description="Customer's support request message")
    channel: Literal["email", "whatsapp", "web"] = Field(..., description="Source channel")
    channel_message_id: str = Field(..., description="Channel-specific message ID for deduplication")

@function_tool
def create_ticket(input: CreateTicketInput) -> dict:
    """
    Create support ticket with channel metadata. MUST be called FIRST in workflow.

    This tool:
    1. Creates/updates customer record by email (primary identifier)
    2. Links channel identifier (phone/whatsapp_id) via customer_identifiers table
    3. Creates conversation with initial_channel tracking
    4. Creates message record with channel, direction='inbound', role='user'
    5. Creates ticket with source_channel and status='pending'

    Returns: ticket_id, conversation_id, customer_id
    """
    # Implementation connects to PostgreSQL, creates records, returns IDs
    pass

class GetCustomerHistoryInput(BaseModel):
    """Input schema for get_customer_history tool"""
    customer_id: str = Field(..., description="Customer UUID from create_ticket response")

@function_tool
def get_customer_history(input: GetCustomerHistoryInput) -> dict:
    """
    Retrieve complete customer history across ALL channels (email, WhatsApp, web).
    MUST be called AFTER create_ticket, BEFORE generating response.

    This tool:
    1. Queries messages table for all conversations linked to customer_id
    2. Includes channel metadata to show cross-channel continuity
    3. Orders by created_at DESC (most recent first)

    Returns: list of messages with channel, content, created_at
    """
    # Implementation queries PostgreSQL, returns message history
    pass

class SearchKnowledgeBaseInput(BaseModel):
    """Input schema for search_knowledge_base tool"""
    query: str = Field(..., description="Customer's question to search in knowledge base")
    top_k: int = Field(default=3, description="Number of top results to return")

@function_tool
def search_knowledge_base(input: SearchKnowledgeBaseInput) -> dict:
    """
    Search product documentation using pgvector semantic similarity.
    Use when customer asks product questions, troubleshooting, account issues.

    This tool:
    1. Generates embedding for query using OpenAI text-embedding-3-small
    2. Performs vector similarity search using pgvector (cosine distance)
    3. Returns top_k most relevant entries with title, content, source_url

    Returns: list of knowledge base entries sorted by relevance
    """
    # Implementation generates embedding, queries PostgreSQL with pgvector
    pass

class SendResponseInput(BaseModel):
    """Input schema for send_response tool"""
    conversation_id: str = Field(..., description="Conversation UUID from create_ticket response")
    channel: Literal["email", "whatsapp", "web"] = Field(..., description="Target channel for response")
    response_text: str = Field(..., description="Response content (will be formatted per channel)")

@function_tool
def send_response(input: SendResponseInput) -> dict:
    """
    Format and deliver response to appropriate channel. MUST be called LAST in workflow.

    This tool automatically formats based on channel parameter:
    - Email: Adds greeting ("Dear {name},"), formats body, adds signature
    - WhatsApp: Concise, conversational tone, splits if > 1600 chars
    - Web: Semi-formal, stores in database + sends email notification

    This tool:
    1. Retrieves conversation and customer details
    2. Applies channel-specific formatting template
    3. Creates outbound message record (direction='outbound', role='assistant')
    4. Sends via channel API (Gmail API, Twilio, web storage)
    5. Updates ticket status to 'responded'

    Returns: message_id, delivery_status
    """
    # Implementation formats response, calls channel API, creates message record
    pass

class EscalateToHumanInput(BaseModel):
    """Input schema for escalate_to_human tool"""
    ticket_id: str = Field(..., description="Ticket UUID to escalate")
    reason: str = Field(..., description="Escalation reason (pricing, refund, legal, sentiment, knowledge_gap)")
    context: str = Field(..., description="Additional context for human agent")

@function_tool
def escalate_to_human(input: EscalateToHumanInput) -> dict:
    """
    Escalate ticket to human support with full context.

    MUST escalate when:
    - Customer mentions "lawyer", "legal", "sue", "attorney"
    - Customer uses profanity or aggressive language
    - Sentiment score < 0.3 (angry/frustrated)
    - Cannot find relevant information after 2 search attempts
    - Customer explicitly requests human help
    - WhatsApp: customer sends "human", "agent", or "representative"

    This tool:
    1. Updates ticket status to 'escalated'
    2. Assigns ticket to human agent queue (assigned_to = escalation_queue_id)
    3. Logs escalation reason and context
    4. Sends notification to customer: "Your request has been escalated to a specialist"

    Returns: escalation_id, estimated_response_time
    """
    # Implementation updates ticket, sends notification
    pass
```

### Kafka Topics & Event Schema

```yaml
# specs/digital-fte/contracts/kafka-topics.md

# Topic: fte.tickets.incoming
# Unified ingestion for all channels
Schema:
  ticket_id: UUID
  conversation_id: UUID
  customer_id: UUID
  channel: enum[email, whatsapp, web]
  message: string
  channel_message_id: string  # For deduplication
  timestamp: ISO8601
  metadata: object  # Channel-specific data

Producers:
  - channels/gmail_handler.py (Gmail webhook)
  - channels/whatsapp_handler.py (Twilio webhook)
  - channels/web_handler.py (Web Form submission)

Consumers:
  - workers/message_processor.py (unified consumer)

# Topic: fte.tickets.gmail (optional channel-specific for analytics)
# Same schema as fte.tickets.incoming with channel='email'

# Topic: fte.tickets.whatsapp (optional channel-specific for analytics)
# Same schema with channel='whatsapp'

# Topic: fte.tickets.web (optional channel-specific for analytics)
# Same schema with channel='web'
```

### API Contracts

```yaml
# specs/digital-fte/contracts/api-endpoints.md

# POST /api/webhooks/gmail
# Gmail Pub/Sub webhook handler
Request:
  Headers:
    - Content-Type: application/json
  Body:
    message:
      data: base64  # Pub/Sub message data
      messageId: string
Response:
  200 OK:
    status: "received"
    ticket_id: UUID
  400 Bad Request:
    error: "Invalid message format"

# POST /api/webhooks/whatsapp
# Twilio WhatsApp webhook handler
Request:
  Headers:
    - Content-Type: application/x-www-form-urlencoded
    - X-Twilio-Signature: string  # MUST validate
  Body:
    From: string  # WhatsApp phone number
    Body: string  # Message content
    MessageSid: string  # Twilio message ID
Response:
  200 OK (TwiML):
    <Response></Response>  # Empty response (agent replies async)
  403 Forbidden:
    error: "Invalid signature"

# POST /api/webhooks/web
# Web Form submission handler
Request:
  Headers:
    - Content-Type: application/json
    - X-CSRF-Token: string  # MUST validate
  Body:
    name: string
    email: string
    message: string
Response:
  201 Created:
    ticket_id: UUID
    status: "pending"
    message: "Your request has been submitted. We'll respond via email shortly."
  400 Bad Request:
    error: "Validation failed"
    fields: object  # Field-specific errors

# GET /api/tickets/{ticket_id}/status
# Check ticket status (for Web Form polling)
Response:
  200 OK:
    ticket_id: UUID
    status: enum[pending, processing, responded, escalated]
    response: string | null  # Available when status='responded'
    created_at: ISO8601
    updated_at: ISO8601
```

### System Architecture Diagram (ASCII)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          CUSTOMER CHANNELS                              │
├─────────────┬──────────────────────┬────────────────────────────────────┤
│   Gmail     │      WhatsApp        │        Web Form                    │
│   (Email)   │    (Messaging)       │       (Website)                    │
└─────┬───────┴──────────┬───────────┴────────────┬───────────────────────┘
      │                  │                        │
      │ Gmail API        │ Twilio API             │ HTTPS POST
      │ Pub/Sub Push     │ Webhook                │ Web Submission
      │                  │                        │
      ▼                  ▼                        ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    FASTAPI SERVICE (API LAYER)                          │
│  ┌────────────────┬─────────────────┬───────────────────────────────┐  │
│  │ /webhooks/     │ /webhooks/      │ /webhooks/web                 │  │
│  │  gmail         │  whatsapp       │ /tickets/{id}/status          │  │
│  │ (Gmail handler)│ (Twilio handler)│ (Web handler)                 │  │
│  └────────┬───────┴────────┬────────┴────────┬──────────────────────┘  │
│           │                 │                 │                         │
│           │  Validate       │  Validate       │  Validate               │
│           │  Pub/Sub msg    │  Twilio sig     │  CSRF token             │
│           │                 │                 │                         │
│  Min 3 replicas, autoscale to 20 (HorizontalPodAutoscaler)             │
└───────────┼─────────────────┼─────────────────┼──────────────────────────┘
            │                 │                 │
            │ Publish to      │ Publish to      │ Publish to
            │ Kafka           │ Kafka           │ Kafka
            ▼                 ▼                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    KAFKA EVENT STREAMING                                │
│  Topics:                                                                │
│  - fte.tickets.incoming (unified)                                       │
│  - fte.tickets.gmail (optional analytics)                               │
│  - fte.tickets.whatsapp (optional analytics)                            │
│  - fte.tickets.web (optional analytics)                                 │
│                                                                         │
│  Guarantees: At-least-once delivery, partitioned by customer_id        │
└────────────────────────────┬────────────────────────────────────────────┘
                             │
                             │ Consume from fte.tickets.incoming
                             ▼
┌─────────────────────────────────────────────────────────────────────────┐
│               MESSAGE PROCESSOR WORKERS (STATELESS)                     │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │  Unified Kafka Consumer                                           │ │
│  │  - Deduplicates by channel_message_id                             │ │
│  │  - Invokes OpenAI Agents SDK with conversation context            │ │
│  │  - Agent calls tools in required order:                           │ │
│  │    1. create_ticket (with channel metadata)                       │ │
│  │    2. get_customer_history (across all channels)                  │ │
│  │    3. search_knowledge_base (if product question)                 │ │
│  │    4. send_response (channel-specific formatting)                 │ │
│  │    OR escalate_to_human (if escalation trigger)                   │ │
│  │  - Records metrics to agent_metrics table                         │ │
│  └───────────────────────────────────────────────────────────────────┘ │
│                                                                         │
│  Min 3 replicas, autoscale to 30 (HorizontalPodAutoscaler)             │
└─────┬───────────────────────────────────────────────┬───────────────────┘
      │                                               │
      │ Read/Write PostgreSQL                         │ Call Channel APIs
      ▼                                               ▼
┌─────────────────────────────────────┐   ┌────────────────────────────────┐
│   POSTGRESQL 16 (CRM DATABASE)      │   │   CHANNEL RESPONSE DELIVERY   │
│   ┌─────────────────────────────┐   │   │  - Gmail API (send email)      │
│   │ Tables:                     │   │   │  - Twilio API (send WhatsApp)  │
│   │ - customers                 │   │   │  - Web storage + email notify  │
│   │ - customer_identifiers      │   │   └────────────────────────────────┘
│   │ - conversations             │   │
│   │ - messages                  │   │
│   │ - tickets                   │   │
│   │ - knowledge_base (pgvector) │   │
│   │ - channel_configs           │   │
│   │ - agent_metrics             │   │
│   └─────────────────────────────┘   │
│   Extensions: pgvector, uuid-ossp   │
│   Replication: Master + Read Replica│
└─────────────────────────────────────┘
```

## Phase 2: Implementation Tasks

### Task Categories

1. **Database Setup** (Priority: P0 - Foundation)
   - Create PostgreSQL database with pgvector extension
   - Run schema.sql to create all tables
   - Seed knowledge_base with sample product documentation
   - Create embeddings for knowledge base entries using OpenAI text-embedding-3-small

2. **Incubation Prototype** (Priority: P1 - Discovery)
   - Build MCP server with 5 tools (create_ticket, get_customer_history, search_knowledge_base, send_response, escalate_to_human)
   - Test with Claude Code using sample customer questions
   - Document edge cases in discovery-log.md
   - Extract prompt patterns and tool schemas

3. **OpenAI Agents SDK Implementation** (Priority: P1 - Core)
   - Convert MCP tools to @function_tool with Pydantic validation
   - Implement customer_success_agent.py with system prompt
   - Create prompts.py with channel-specific templates
   - Add error handling and graceful fallbacks for all external calls

4. **Channel Integrations** (Priority: P1 - Channels)
   - Gmail: Set up Google Cloud project, enable Gmail API, configure Pub/Sub, implement gmail_handler.py
   - WhatsApp: Set up Twilio account, configure WhatsApp sandbox, implement whatsapp_handler.py with signature validation
   - Web Form: Build React/Next.js SupportForm.jsx with validation, implement web_handler.py

5. **Kafka Event Streaming** (Priority: P1 - Architecture)
   - Set up Kafka cluster (Confluent Cloud or self-hosted)
   - Create topics: fte.tickets.incoming, fte.tickets.gmail, fte.tickets.whatsapp, fte.tickets.web
   - Implement kafka_client.py producer
   - Implement kafka_client.py consumer with consumer group

6. **FastAPI Service** (Priority: P1 - API)
   - Create main.py with FastAPI app
   - Implement webhook routes for Gmail, WhatsApp, Web Form
   - Add authentication middleware and structured logging
   - Implement health check and readiness probe endpoints

7. **Message Processor Workers** (Priority: P1 - Workers)
   - Implement message_processor.py unified Kafka consumer
   - Add deduplication logic using channel_message_id
   - Implement response_sender.py for channel-specific delivery
   - Add metrics recording to agent_metrics table

8. **Kubernetes Deployment** (Priority: P2 - Infrastructure)
   - Create Dockerfiles for API and worker services
   - Write k8s manifests: deployments, services, HPA, ConfigMaps, Secrets
   - Deploy to Minikube/cloud cluster
   - Validate autoscaling (3 → 20 API pods, 3 → 30 worker pods)

9. **Testing** (Priority: P2 - Quality)
   - Unit tests: test_tools.py, test_channels.py, test_models.py (> 80% coverage)
   - Integration tests: test_gmail_flow.py, test_whatsapp_flow.py, test_web_flow.py, test_cross_channel.py
   - Chaos tests: test_pod_kills.py (kill random pods every 2h)
   - Load tests: k6_load_test.js (100+ concurrent users)

10. **24-Hour Continuous Operation Test** (Priority: P3 - Validation)
    - Run chaos testing script (pod kills every 2h)
    - Load test with 100+ web submissions, 50+ emails, 50+ WhatsApp messages
    - Monitor uptime, latency, escalation rate, message loss
    - Validate cross-channel customer identification (10+ customers)

## Complexity Tracking

No violations of constitution principles. All architectural decisions align with:
- Multi-channel requirement satisfied (Gmail, WhatsApp, Web Form)
- PostgreSQL as CRM (no external CRM)
- Kafka event streaming for reliability
- Kubernetes autoscaling for operational excellence
- OpenAI Agents SDK for AI behavior standards

## Risk Mitigation

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Gmail API quota exceeded | Medium | High | Exponential backoff, Kafka retry queue, upgrade to paid tier |
| Cross-channel ID < 95% accuracy | Low | High | Fuzzy phone matching, customer confirmation prompt |
| Knowledge base search quality poor | Medium | Medium | Curate docs, tune chunk size, semantic caching |
| Autoscaling too slow (latency > 3s) | Low | Medium | Pre-warm 3 replicas, tune HPA metrics |
| Kafka broker failure (message loss) | Low | High | Replication factor 3, acks=all, monitor lag |
| Web Form CSRF vulnerability | Medium | High | Implement token validation, rate limiting |
| Twilio signature validation bypass | Low | Critical | Strict signature verification, HTTPS only |
| PostgreSQL connection pool exhaustion | Medium | High | Tune pool size, implement circuit breaker |

## Next Steps

1. **Create tasks.md** with actionable, testable tasks and dependency graph
2. **Set up development environment** with Docker Compose (PostgreSQL, Kafka, localstack)
3. **Start Stage 1 Incubation** with Claude Code MCP server exploration
4. **Document discoveries** in discovery-log.md as edge cases emerge
5. **Transition to Stage 2** when all incubation deliverables complete
