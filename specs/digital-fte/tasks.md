---
description: "Actionable tasks for Digital FTE Customer Success Agent implementation"
---

# Tasks: Digital FTE Customer Success Agent

**Input**: Design documents from `/specs/digital-fte/`
**Prerequisites**: plan.md (✅), spec.md (✅), constitution.md (✅)

**Tests**: All testing phases included per constitution requirement (> 80% coverage, E2E, chaos, 24-hour validation)

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story per SpecKit Plus methodology.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1=Web Form, US2=Gmail, US3=WhatsApp, US4=Cross-Channel, US5=24h Test)
- Include exact file paths in descriptions

## Path Conventions

- **Web app structure**: `backend/src/`, `frontend/src/`, `k8s/`
- **Incubation stage**: `incubation/` (temporary, deleted after Stage 2 transition)
- **Database**: `backend/src/database/`
- **Tests**: `backend/tests/`, `frontend/tests/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure per plan.md

- [ ] T001 Create project directory structure (backend/, frontend/, k8s/, incubation/, specs/)
- [ ] T002 [P] Initialize Python project with requirements.txt (FastAPI, OpenAI SDK, Pydantic, psycopg2, kafka-python)
- [ ] T003 [P] Initialize Node.js project with package.json (React, Next.js, Tailwind CSS)
- [ ] T004 [P] Configure .env.example with all required environment variables (DATABASE_URL, KAFKA_BROKER, OPENAI_API_KEY, etc.)
- [ ] T005 [P] Create docker-compose.yml for local development (PostgreSQL, Kafka, Zookeeper)
- [ ] T006 [P] Configure .gitignore (exclude .env, __pycache__, node_modules, .next)
- [ ] T007 [P] Create README.md with project overview and quickstart guide

**Checkpoint**: Project structure ready for foundational development

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Database Foundation

- [ ] T008 Create backend/src/database/schema.sql with complete PostgreSQL schema (customers, customer_identifiers, conversations, messages, tickets, knowledge_base, channel_configs, agent_metrics)
- [ ] T009 Create backend/src/database/migrations/ directory with V001_initial_schema.sql migration script
- [ ] T010 Create backend/src/database/connection.py with PostgreSQL connection pool management (asyncpg, max 20 connections)
- [ ] T011 Create backend/src/database/seed_knowledge_base.py script to populate knowledge_base with sample product docs
- [ ] T012 Create backend/src/database/generate_embeddings.py to create pgvector embeddings for knowledge base using OpenAI text-embedding-3-small

### Kafka Foundation

- [ ] T013 [P] Create backend/src/kafka/topics.py with topic definitions (fte.tickets.incoming, fte.tickets.gmail, fte.tickets.whatsapp, fte.tickets.web)
- [ ] T014 [P] Create backend/src/kafka/producer.py with Kafka producer client (async, error handling)
- [ ] T015 [P] Create backend/src/kafka/consumer.py with Kafka consumer client (consumer group, offset management)

### Pydantic Models

- [ ] T016 [P] Create backend/src/models/customer.py with Customer and CustomerIdentifier Pydantic models
- [ ] T017 [P] Create backend/src/models/conversation.py with Conversation Pydantic model
- [ ] T018 [P] Create backend/src/models/message.py with Message Pydantic model
- [ ] T019 [P] Create backend/src/models/ticket.py with Ticket Pydantic model
- [ ] T020 [P] Create backend/src/models/knowledge_base.py with KnowledgeBaseEntry Pydantic model

### Utilities & Configuration

- [ ] T021 [P] Create backend/src/utils/config.py with environment configuration management (Pydantic Settings)
- [ ] T022 [P] Create backend/src/utils/logger.py with structured logging setup (JSON format, conversation_id/customer_id/channel context)
- [ ] T023 [P] Create backend/src/utils/validators.py with custom Pydantic validators (email, phone, channel enums)

### Incubation Stage 1 (MCP Server - Discovery)

- [ ] T024 Create incubation/mcp_server.py with Model Context Protocol server skeleton
- [ ] T025 [P] Create incubation/tools/create_ticket.py with initial tool definition
- [ ] T026 [P] Create incubation/tools/get_customer_history.py with initial tool definition
- [ ] T027 [P] Create incubation/tools/search_knowledge_base.py with initial tool definition
- [ ] T028 [P] Create incubation/tools/send_response.py with initial tool definition
- [ ] T029 [P] Create incubation/tools/escalate_to_human.py with initial tool definition
- [ ] T030 Create incubation/test_scenarios/ directory with edge case test files (pricing_questions.txt, refund_requests.txt, cross_channel_scenarios.txt, angry_customers.txt)
- [ ] T031 Test MCP server with Claude Code using sample customer questions from all three channels
- [ ] T032 Document edge cases and prompt patterns in specs/digital-fte/discovery-log.md

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Customer Submits Web Form Support Request (Priority: P1) 🎯 MVP

**Goal**: MANDATORY Web Support Form component that accepts customer questions and delivers AI responses via web interface and email notification

**Independent Test**: Deploy React component, submit form with test question, verify Digital FTE processes and responds via email

### Tests for User Story 1 (Write FIRST, ensure FAIL before implementation)

- [ ] T033 [P] [US1] Create frontend/tests/SupportForm.test.jsx with React Testing Library tests (form validation, submission, status display)
- [ ] T034 [P] [US1] Create backend/tests/integration/test_web_flow.py with E2E test (form submission → Kafka → agent → response → email)

### Implementation for User Story 1

- [ ] T035 [P] [US1] Create frontend/src/components/SupportForm.jsx with form fields (name, email, message), client-side validation (required fields, email format)
- [ ] T036 [P] [US1] Create frontend/src/components/FormValidation.js with validation logic (max lengths, sanitization)
- [ ] T037 [P] [US1] Create frontend/src/components/StatusDisplay.jsx with ticket status component (Pending, Processing, Responded, Escalated)
- [ ] T038 [P] [US1] Create frontend/src/services/api.js with backend API client (fetch wrapper with error handling)
- [ ] T039 [US1] Create frontend/src/pages/index.jsx with support page entry point integrating SupportForm
- [ ] T040 [US1] Create frontend/src/styles/support-form.css with form styling (mobile-responsive, accessible)
- [ ] T041 [US1] Create backend/src/channels/web_handler.py with Web Form submission handler (validate CSRF token, create customer, publish to Kafka)
- [ ] T042 [US1] Create backend/src/api/routes/web.py with POST /api/webhooks/web endpoint and GET /api/tickets/{ticket_id}/status endpoint
- [ ] T043 [US1] Add logging for web form operations in web_handler.py (structured logs with submission_id, customer_id)
- [ ] T044 [US1] Test Web Form submission independently (submit → verify Kafka message → verify email sent)

**Checkpoint**: At this point, User Story 1 (Web Form) should be fully functional and testable independently

---

## Phase 4: User Story 2 - Customer Emails Support via Gmail (Priority: P1)

**Goal**: Gmail integration with Pub/Sub webhooks that receives customer emails, processes with Digital FTE, and sends formatted email responses

**Independent Test**: Send email to support@company.com, verify Gmail webhook receives it, Digital FTE processes, and formatted reply sent via Gmail API

### Tests for User Story 2 (Write FIRST, ensure FAIL before implementation)

- [ ] T045 [P] [US2] Create backend/tests/integration/test_gmail_flow.py with E2E test (Gmail webhook → Kafka → agent → Gmail API send)
- [ ] T046 [P] [US2] Create backend/tests/unit/test_gmail_handler.py with unit tests (Pub/Sub message parsing, signature validation)

### Implementation for User Story 2

- [ ] T047 [US2] Set up Google Cloud project with Gmail API enabled, create OAuth2 credentials
- [ ] T048 [US2] Configure Gmail Pub/Sub topic and subscription for push notifications
- [ ] T049 [US2] Create backend/src/channels/gmail_handler.py with Gmail Pub/Sub webhook handler (parse message, extract sender/subject/body, publish to Kafka)
- [ ] T050 [US2] Implement Gmail API send functionality in gmail_handler.py (format email with greeting/signature, send via Gmail API)
- [ ] T051 [US2] Create backend/src/api/routes/gmail.py with POST /api/webhooks/gmail endpoint (validate Pub/Sub message, call handler)
- [ ] T052 [US2] Add email formatting templates in backend/src/agent/prompts.py (formal greeting: "Dear {name},", signature: "Best regards, Customer Success Team")
- [ ] T053 [US2] Add error handling for Gmail API quota limits (exponential backoff, Kafka retry queue)
- [ ] T054 [US2] Add logging for Gmail operations (message_id, customer_id, channel='email')
- [ ] T055 [US2] Test Gmail flow independently (send email → verify webhook → verify formatted reply received)

**Checkpoint**: At this point, User Stories 1 (Web) AND 2 (Gmail) should both work independently

---

## Phase 5: User Story 3 - Customer Sends WhatsApp Message (Priority: P2)

**Goal**: WhatsApp integration via Twilio that receives messages, validates signatures, processes with concise responses, and sends via Twilio API

**Independent Test**: Send WhatsApp message to Twilio number, verify webhook signature validation, Digital FTE processes, and concise reply sent

### Tests for User Story 3 (Write FIRST, ensure FAIL before implementation)

- [ ] T056 [P] [US3] Create backend/tests/integration/test_whatsapp_flow.py with E2E test (Twilio webhook → Kafka → agent → Twilio send)
- [ ] T057 [P] [US3] Create backend/tests/unit/test_whatsapp_handler.py with unit tests (signature validation, message splitting > 1600 chars)

### Implementation for User Story 3

- [ ] T058 [US3] Set up Twilio account with WhatsApp sandbox or approved number
- [ ] T059 [US3] Create backend/src/channels/whatsapp_handler.py with Twilio webhook handler (validate X-Twilio-Signature, parse From/Body/MessageSid, publish to Kafka)
- [ ] T060 [US3] Implement Twilio API send functionality in whatsapp_handler.py (send concise response, split if > 1600 chars)
- [ ] T061 [US3] Create backend/src/api/routes/whatsapp.py with POST /api/webhooks/whatsapp endpoint (validate signature, return empty TwiML response)
- [ ] T062 [US3] Add WhatsApp formatting templates in backend/src/agent/prompts.py (concise, conversational, no formal greeting, max 300 chars preferred)
- [ ] T063 [US3] Add escalation keyword detection in whatsapp_handler.py (keywords: "human", "agent", "representative")
- [ ] T064 [US3] Add logging for WhatsApp operations (MessageSid, customer_id, channel='whatsapp')
- [ ] T065 [US3] Test WhatsApp flow independently (send message → verify signature validation → verify concise reply received)

**Checkpoint**: At this point, User Stories 1 (Web), 2 (Gmail), AND 3 (WhatsApp) should all work independently

---

## Phase 6: User Story 4 - Cross-Channel Customer Continuity (Priority: P1)

**Goal**: Cross-channel customer identification with > 95% accuracy, enabling customer history retrieval across email, WhatsApp, and web form

**Independent Test**: Create customer via email, send WhatsApp message with linked phone, verify customer_identifiers table links them, and history includes both channels

### Tests for User Story 4 (Write FIRST, ensure FAIL before implementation)

- [ ] T066 [P] [US4] Create backend/tests/integration/test_cross_channel.py with cross-channel customer ID test (email → WhatsApp → web with same customer)
- [ ] T067 [P] [US4] Create backend/tests/unit/test_customer_linking.py with unit tests (email matching, phone normalization, fuzzy matching)

### Implementation for User Story 4

- [ ] T068 [US4] Implement customer lookup/create logic in backend/src/channels/web_handler.py (check customers table by email, create if not exists)
- [ ] T069 [US4] Implement customer identifier linking in backend/src/channels/gmail_handler.py (insert into customer_identifiers with identifier_type='email')
- [ ] T070 [US4] Implement customer identifier linking in backend/src/channels/whatsapp_handler.py (normalize phone number, insert into customer_identifiers with identifier_type='phone')
- [ ] T071 [US4] Create backend/src/utils/phone_normalizer.py with phone number normalization logic (remove formatting, country code handling)
- [ ] T072 [US4] Create backend/src/utils/fuzzy_matcher.py with fuzzy matching for customer identification (Levenshtein distance for phone numbers)
- [ ] T073 [US4] Add customer identity confirmation prompt in agent prompts.py ("Is this the same person who contacted us via {previous_channel}?")
- [ ] T074 [US4] Test cross-channel identification (create via email → contact via WhatsApp → verify customer_id matches, history retrieved)

**Checkpoint**: All user stories should now support cross-channel customer continuity

---

## Phase 7: OpenAI Agents SDK Implementation (Stage 2 Specialization)

**Goal**: Convert incubation MCP tools to production OpenAI Agents SDK with Pydantic validation, error handling, and channel-aware responses

**Independent Test**: Message processor consumes from Kafka, calls agent with tools, agent follows required workflow order, response delivered to correct channel

### Agent Tools Implementation

- [ ] T075 [P] Create backend/src/agent/tools.py with @function_tool decorators for all 5 tools
- [ ] T076 [P] Implement create_ticket tool in tools.py with CreateTicketInput Pydantic schema (connects to PostgreSQL, creates customer/conversation/message/ticket)
- [ ] T077 [P] Implement get_customer_history tool in tools.py with GetCustomerHistoryInput schema (queries messages table across all channels)
- [ ] T078 [P] Implement search_knowledge_base tool in tools.py with SearchKnowledgeBaseInput schema (generates embedding, pgvector cosine similarity search)
- [ ] T079 [P] Implement send_response tool in tools.py with SendResponseInput schema (applies channel-specific formatting, calls channel API, creates outbound message)
- [ ] T080 [P] Implement escalate_to_human tool in tools.py with EscalateToHumanInput schema (updates ticket status, sends customer notification)

### Agent Implementation

- [ ] T081 Create backend/src/agent/customer_success_agent.py with OpenAI Agents SDK implementation (GPT-4o, tool bindings)
- [ ] T082 Create backend/src/agent/prompts.py with system prompt templates (channel context, hard constraints, escalation triggers, workflow order)
- [ ] T083 Add sentiment analysis to agent logic (detect angry/frustrated customers with score < 0.3, trigger escalation)
- [ ] T084 Add legal keyword detection to agent logic (keywords: "lawyer", "legal", "sue", "attorney" → immediate escalation)
- [ ] T085 Add knowledge base retry logic to agent (max 2 search attempts, escalate if no results)
- [ ] T086 Add error handling for all tool calls (try/catch with graceful fallbacks, log errors with context)

### Message Processor Workers

- [ ] T087 Create backend/src/workers/message_processor.py with unified Kafka consumer (consumes from fte.tickets.incoming)
- [ ] T088 Implement deduplication logic in message_processor.py (check messages table for existing channel_message_id, skip if exists)
- [ ] T089 Implement agent invocation in message_processor.py (pass conversation context, monitor tool calls)
- [ ] T090 Create backend/src/workers/response_sender.py with channel-specific delivery (route to gmail_handler/whatsapp_handler/web_handler based on channel)
- [ ] T091 Add metrics recording in message_processor.py (insert into agent_metrics table: response_time_ms, escalation, sentiment_score, tool_calls JSON)
- [ ] T092 Add structured logging in message_processor.py (conversation_id, customer_id, channel, tool_call sequence)

**Checkpoint**: OpenAI Agents SDK fully operational, processing messages from all channels with required workflow order

---

## Phase 8: FastAPI Service & Kubernetes Deployment

**Goal**: Production-ready FastAPI service with all channel endpoints, deployed to Kubernetes with autoscaling and monitoring

### FastAPI Service

- [ ] T093 Create backend/src/api/main.py with FastAPI app entry point (CORS, middleware, health check, readiness probe)
- [ ] T094 Create backend/src/api/middleware/auth.py with API authentication (API key validation for non-webhook endpoints)
- [ ] T095 Create backend/src/api/middleware/logging.py with request/response logging middleware (structured logs with request_id)
- [ ] T096 [P] Register all route modules in main.py (gmail.py, whatsapp.py, web.py)
- [ ] T097 [P] Add health check endpoint GET /health (returns 200 OK, checks PostgreSQL/Kafka connectivity)
- [ ] T098 [P] Add readiness probe endpoint GET /ready (returns 200 when all dependencies ready)

### Docker & Docker Compose

- [ ] T099 Create backend/Dockerfile with multi-stage build (Python 3.11 slim, install dependencies, copy source)
- [ ] T100 Create frontend/Dockerfile with multi-stage build (Node.js 18, build Next.js, serve static)
- [ ] T101 Update docker-compose.yml to include API and worker services (depends_on: PostgreSQL, Kafka)
- [ ] T102 Test local development with docker-compose up (verify all services start, endpoints accessible)

### Kubernetes Manifests

- [ ] T103 [P] Create k8s/namespace.yaml with digital-fte namespace
- [ ] T104 [P] Create k8s/configmap.yaml with environment configuration (DATABASE_HOST, KAFKA_BROKER, non-sensitive config)
- [ ] T105 [P] Create k8s/secrets.yaml with secrets template (DATABASE_PASSWORD, OPENAI_API_KEY, GMAIL_CREDENTIALS, TWILIO_AUTH_TOKEN)
- [ ] T106 Create k8s/postgres-statefulset.yaml with PostgreSQL StatefulSet (persistent volume, pgvector extension)
- [ ] T107 Create k8s/postgres-service.yaml with PostgreSQL ClusterIP service
- [ ] T108 Create k8s/api-deployment.yaml with API deployment (min 3 replicas, health check, readiness probe, resource limits)
- [ ] T109 Create k8s/worker-deployment.yaml with worker deployment (min 3 replicas, resource limits, environment variables)
- [ ] T110 Create k8s/api-service.yaml with API LoadBalancer service (expose port 80/443)
- [ ] T111 Create k8s/api-hpa.yaml with HorizontalPodAutoscaler for API (min 3, max 20, target CPU 70%)
- [ ] T112 Create k8s/worker-hpa.yaml with HorizontalPodAutoscaler for workers (min 3, max 30, target CPU 70%)
- [ ] T113 [P] Create k8s/ingress.yaml with Ingress for Web Form (SSL termination, routing rules)
- [ ] T114 Deploy to Kubernetes cluster (kubectl apply -f k8s/), verify all pods running
- [ ] T115 Test autoscaling (generate load, verify API scales from 3 → 10+ pods, workers scale from 3 → 10+)

**Checkpoint**: Production deployment complete, autoscaling validated

---

## Phase 9: Testing & Quality Assurance

**Goal**: Comprehensive testing suite with > 80% coverage, E2E tests for all channels, chaos tests, and load tests

### Unit Tests

- [ ] T116 [P] Create backend/tests/unit/test_tools.py with tests for all 5 agent tools (mock PostgreSQL, mock APIs)
- [ ] T117 [P] Create backend/tests/unit/test_models.py with Pydantic model validation tests (edge cases, invalid inputs)
- [ ] T118 [P] Create backend/tests/unit/test_validators.py with custom validator tests (email, phone normalization)
- [ ] T119 [P] Create backend/tests/unit/test_kafka_producer.py with Kafka producer tests (mock broker, verify message format)
- [ ] T120 [P] Create backend/tests/unit/test_kafka_consumer.py with Kafka consumer tests (mock messages, verify processing)

### Integration Tests (Already created in user story phases, verify passing)

- [ ] T121 Run backend/tests/integration/test_web_flow.py (Web Form E2E test)
- [ ] T122 Run backend/tests/integration/test_gmail_flow.py (Gmail E2E test)
- [ ] T123 Run backend/tests/integration/test_whatsapp_flow.py (WhatsApp E2E test)
- [ ] T124 Run backend/tests/integration/test_cross_channel.py (Cross-channel customer ID test)

### Chaos Tests

- [ ] T125 Create backend/tests/chaos/test_pod_kills.py with chaos engineering test (kill random pod every 2 hours, verify zero message loss)
- [ ] T126 Create backend/tests/chaos/kill_random_pod.sh script (select random API/worker pod, kubectl delete pod)
- [ ] T127 Run chaos test for 6 hours (3 pod kills), verify uptime > 99.9%, no messages dropped from Kafka

### Load Tests

- [ ] T128 Create backend/tests/load/k6_load_test.js with K6 load test script (100 concurrent users, ramp up over 5 minutes)
- [ ] T129 Run load test against Web Form endpoint (100+ submissions, verify P95 latency < 3 seconds)
- [ ] T130 Run load test against Gmail webhook endpoint (50+ messages, verify processing time)
- [ ] T131 Run load test against WhatsApp webhook endpoint (50+ messages, verify concise responses)
- [ ] T132 Monitor autoscaling during load test (verify HPA scales API/workers appropriately)

### Code Coverage

- [ ] T133 Install pytest-cov for Python coverage analysis
- [ ] T134 Run pytest with coverage (pytest --cov=backend/src --cov-report=html)
- [ ] T135 Verify > 80% code coverage (add tests for uncovered branches if needed)

**Checkpoint**: All tests passing, > 80% coverage, chaos resilience validated

---

## Phase 10: User Story 5 - 24-Hour Continuous Operation Test (Priority: P1) 🎯 FINAL CHALLENGE

**Goal**: Validate production-readiness with 24-hour continuous operation test: 100+ web submissions, 50+ emails, 50+ WhatsApp messages, 10+ cross-channel customers, uptime > 99.9%, P95 latency < 3s

**Independent Test**: This IS the final validation test that proves Digital FTE meets all success criteria

### Test Preparation

- [ ] T136 Create backend/tests/24h/load_generator.py script (generates realistic customer questions across all channels)
- [ ] T137 Create backend/tests/24h/chaos_runner.py script (kills random pod every 2 hours)
- [ ] T138 Create backend/tests/24h/metrics_collector.py script (records uptime, latency, escalation rate, message loss)
- [ ] T139 Seed knowledge_base with comprehensive product documentation (100+ entries covering common questions)

### 24-Hour Test Execution

- [ ] T140 Start 24-hour test timer (timestamp: start_time)
- [ ] T141 Start chaos_runner.py (kills random pod every 2 hours → 12 pod kills over 24 hours)
- [ ] T142 Start load_generator.py with Web Form load (100+ submissions over 24 hours)
- [ ] T143 Start load_generator.py with Gmail load (50+ emails over 24 hours)
- [ ] T144 Start load_generator.py with WhatsApp load (50+ messages over 24 hours)
- [ ] T145 Include cross-channel scenarios (10+ customers using multiple channels: email → WhatsApp → web)
- [ ] T146 Monitor metrics_collector.py in real-time (uptime, latency, escalation rate, message loss)

### Test Validation

- [ ] T147 After 24 hours, stop all test scripts (timestamp: end_time)
- [ ] T148 Verify uptime > 99.9% (max downtime: 86 seconds over 24 hours)
- [ ] T149 Verify P95 latency < 3 seconds for all channels (query agent_metrics table)
- [ ] T150 Verify escalation rate < 25% (query tickets table: escalated / total)
- [ ] T151 Verify zero message loss (compare Kafka offset vs messages table count)
- [ ] T152 Verify cross-channel ID accuracy > 95% (query customer_identifiers table for correct linking)
- [ ] T153 Verify Web Form: 100+ submissions processed successfully
- [ ] T154 Verify Gmail: 50+ emails processed successfully
- [ ] T155 Verify WhatsApp: 50+ messages processed successfully
- [ ] T156 Verify cross-channel: 10+ customers correctly identified across multiple channels
- [ ] T157 Generate 24-hour test report (uptime, latency, escalation rate, message loss, cross-channel accuracy)

**Checkpoint**: 24-hour continuous operation test PASSED → Digital FTE is production-ready

---

## Phase 11: Documentation & Polish

**Purpose**: Final documentation, cleanup, and deployment guide

- [ ] T158 [P] Update README.md with complete setup instructions (prerequisites, installation, configuration)
- [ ] T159 [P] Create docs/DEPLOYMENT.md with Kubernetes deployment guide (cluster setup, secrets, kubectl apply)
- [ ] T160 [P] Create docs/RUNBOOK.md with incident response procedures (pod crash, Kafka broker down, PostgreSQL connection pool exhausted)
- [ ] T161 [P] Create docs/API.md with API endpoint documentation (all webhooks, request/response schemas)
- [ ] T162 [P] Create docs/AGENT_TOOLS.md with agent tool documentation (all 5 tools, input schemas, workflows)
- [ ] T163 Delete incubation/ directory (MCP server no longer needed after Stage 2 transition)
- [ ] T164 Create .env.production.example with production environment variables template
- [ ] T165 Code cleanup and refactoring (remove debug logs, optimize imports, format code)
- [ ] T166 Security hardening (verify no secrets in code, audit dependencies for vulnerabilities)
- [ ] T167 Performance optimization (database query optimization, Kafka producer batching)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phases 3-6)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **OpenAI Agents SDK (Phase 7)**: Depends on Foundational completion, benefits from incubation (T024-T032)
- **Deployment (Phase 8)**: Depends on Agents SDK implementation
- **Testing (Phase 9)**: Depends on Deployment completion
- **24-Hour Test (Phase 10)**: Depends on Testing phase passing
- **Documentation (Phase 11)**: Depends on 24-hour test passing

### User Story Dependencies

- **User Story 1 (Web Form - P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (Gmail - P1)**: Can start after Foundational (Phase 2) - Independent from US1
- **User Story 3 (WhatsApp - P2)**: Can start after Foundational (Phase 2) - Independent from US1/US2
- **User Story 4 (Cross-Channel - P1)**: Depends on US1, US2, US3 channel handlers being implemented (needs all three channels for linking)
- **User Story 5 (24h Test - P1)**: Depends on ALL previous stories being complete and tested

### Within Each Phase

- Setup tasks marked [P] can run in parallel
- Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user story phases (3-6) can start in parallel
- Tests for each user story MUST be written and FAIL before implementation
- Models before services, services before endpoints, core before integration

### Parallel Opportunities

#### Phase 2 (Foundational) - Can run in parallel:
- T016-T020 (all Pydantic models)
- T021-T023 (all utility modules)
- T024-T029 (all MCP tool definitions)

#### Phase 3 (Web Form) - Can run in parallel:
- T033-T034 (tests)
- T035-T040 (all frontend components)

#### Phase 7 (Agent Tools) - Can run in parallel:
- T075-T080 (all 5 tool implementations)

#### Phase 8 (Kubernetes) - Can run in parallel:
- T103-T105 (namespace, configmap, secrets)
- T097-T098 (health check, readiness probe)

#### Phase 9 (Unit Tests) - Can run in parallel:
- T116-T120 (all unit test files)

---

## Implementation Strategy

### MVP First (Incubation → Web Form Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (including incubation T024-T032)
3. Complete Phase 3: User Story 1 (Web Form)
4. Complete Phase 7: OpenAI Agents SDK (enough for Web Form processing)
5. **STOP and VALIDATE**: Test Web Form independently with agent
6. Deploy to local Kubernetes (Phase 8 minimal)

### Full Multi-Channel Build

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 (Web Form) → Test independently → MVP deployed
3. Add User Story 2 (Gmail) → Test independently
4. Add User Story 3 (WhatsApp) → Test independently
5. Add User Story 4 (Cross-Channel) → Test all channels together
6. Complete OpenAI Agents SDK implementation (Phase 7)
7. Deploy to Kubernetes with autoscaling (Phase 8)
8. Run comprehensive testing (Phase 9)
9. Execute 24-hour continuous operation test (Phase 10)
10. Polish and document (Phase 11)

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Web Form) + Frontend
   - Developer B: User Story 2 (Gmail) + Backend API
   - Developer C: User Story 3 (WhatsApp) + Backend API
3. Developer D (or A/B/C after stories complete): Phase 7 (OpenAI Agents SDK)
4. Team integrates and tests together (Phase 9-10)

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing (TDD approach)
- Commit after each task or logical group of tasks
- Stop at any checkpoint to validate story independently
- **MANDATORY deliverable**: Web Support Form (User Story 1) - highest priority
- **FINAL CHALLENGE**: 24-hour continuous operation test (User Story 5) - proves production-readiness
- Follow SpecKit Plus workflow: constitution (✅) → specify (✅) → plan (✅) → tasks (✅) → implement (NEXT)
- Incubation → Specialization transition after T032 (discovery-log.md complete)
- Delete incubation/ directory after Phase 7 complete (T163)

---

**Total Tasks**: 167 tasks across 11 phases
**Estimated Timeline**: 48-72 development hours (single developer)
**Success Criteria**: All 167 tasks complete + 24-hour test passing (T140-T157)
