# Digital FTE Customer Success Agent Constitution

## Core Principles

### I. Customer Experience First
**Channel-Appropriate Communication**: Every customer touchpoint must respect the channel's norms:
- Email: Formal, detailed, with greeting and signature (max 500 words)
- WhatsApp: Concise, conversational, friendly (max 300 characters preferred)
- Web Form: Semi-formal, helpful, balanced (max 300 words)

**Cross-Channel Continuity**: Customer history is preserved regardless of which channel they use. Email is the primary identifier for customer identity across all channels.

**Intelligent Escalation**: Complex issues (pricing, refunds, legal, sentiment < 0.3) must be escalated to humans with full context. Escalation rate target: < 20%.

**24/7 Availability**: The Digital FTE operates continuously without downtime. Target uptime: > 99.9%.

### II. Reliability & Operational Excellence
**No Single Point of Failure**: All components must be redundant:
- API pods: min 3 replicas, autoscale to 20
- Worker pods: min 3 replicas, autoscale to 30
- Kafka: distributed message queue
- PostgreSQL: production-grade with replication

**Graceful Degradation**: System continues operating even if individual channels fail. Errors in one channel must not affect others.

**Chaos Resilience**: Must survive random pod kills every 2 hours. All workers are stateless; all state is in PostgreSQL.

**Observability**: Every interaction logged with:
- Conversation ID
- Customer ID
- Channel metadata
- Tool calls
- Latency metrics
- Sentiment scores

### III. Data Integrity & Privacy
**Unified Customer Identity**:
- Email is primary identifier
- Phone numbers linked via customer_identifiers table
- Cross-channel matching > 95% accuracy

**Complete Audit Trail**:
- Every message stored in messages table with channel, direction, role
- Every tool call recorded with inputs/outputs
- Channel message IDs preserved for tracking

**Zero Data Loss**: Kafka guarantees at-least-once delivery. Idempotent processing ensures no duplicate responses.

**Privacy**: No hardcoded credentials. All secrets in Kubernetes secrets. Support GDPR data export/deletion.

### IV. Multi-Channel Architecture (NON-NEGOTIABLE)
**Unified Ticket Ingestion**:
- All channels publish to `fte.tickets.incoming` Kafka topic
- Unified message processor consumes from single queue
- Channel metadata preserved throughout lifecycle

**Three Channels Required**:
1. **Gmail** (Email): Gmail API + Pub/Sub push notifications, webhook handler, send via Gmail API
2. **WhatsApp** (Messaging): Twilio WhatsApp API, webhook with signature validation, reply via Twilio
3. **Web Form** (Website): REQUIRED - Complete React/Next.js component with validation, submission, status checking

**Channel-Specific Response Formatting**:
- Agent uses single `send_response` tool
- Tool automatically formats based on channel parameter
- Email: greeting + body + signature
- WhatsApp: concise, split if > 1600 chars
- Web: stored for API retrieval + email notification

### V. PostgreSQL as CRM (NO EXTERNAL CRM)
**Database Schema IS the CRM**:
```
- customers: Unified customer records
- customer_identifiers: Cross-channel linking (email, phone, whatsapp)
- conversations: Interaction sessions with initial_channel tracking
- messages: All messages with channel, direction, role
- tickets: Support tickets with source_channel
- knowledge_base: Product docs with pgvector embeddings
- channel_configs: Per-channel configuration
- agent_metrics: Performance tracking by channel
```

**No Salesforce, No HubSpot**: PostgreSQL provides all CRM functionality needed for this hackathon.

### VI. AI Agent Behavior Standards
**Hard Constraints (NEVER violate)**:
- NEVER discuss pricing → escalate immediately
- NEVER promise features not in documentation
- NEVER process refunds → escalate to billing
- NEVER share internal processes or system details
- ALWAYS create ticket before responding (with channel metadata)
- ALWAYS check customer history across ALL channels
- ALWAYS use send_response tool (ensures channel formatting)
- ALWAYS respect channel response limits

**Escalation Triggers (MUST escalate)**:
- Customer mentions "lawyer", "legal", "sue", or "attorney"
- Customer uses profanity or aggressive language
- Sentiment score < 0.3 (angry/frustrated)
- Cannot find relevant information after 2 search attempts
- Customer explicitly requests human help
- WhatsApp: customer sends "human", "agent", or "representative"

**Required Workflow Order**:
1. FIRST: create_ticket (with channel)
2. THEN: get_customer_history (across all channels)
3. THEN: search_knowledge_base (if product question)
4. FINALLY: send_response (with channel parameter)

### VII. Development Workflow: Incubation → Specialization
**Stage 1: Incubation (Hours 1-16) - Claude Code Exploration**:
- Use Claude Code as Agent Factory to explore problem space
- Build working prototype with MCP server
- Discover edge cases through iterative testing
- Document all findings in specs/discovery-log.md
- Create crystallized specs/customer-success-fte-spec.md
- Define agent skills manifest
- Identify channel-specific patterns

**Stage 2: Specialization (Hours 17-40) - Production Build**:
- Transform MCP tools to OpenAI Agents SDK @function_tool
- Add Pydantic input validation to all tools
- Add comprehensive error handling with fallbacks
- Build all three channel integrations (Gmail, WhatsApp, Web Form)
- Deploy to Kubernetes with autoscaling
- Set up Kafka event streaming
- Create FastAPI service with channel endpoints

**Transition Criteria**:
- ✓ All transition tests passing
- ✓ Prompts extracted to prompts.py
- ✓ Tools have Pydantic BaseModel inputs
- ✓ Error handling for all external calls
- ✓ Edge cases documented with test cases
- ✓ Production folder structure created

### VIII. Testing & Quality Gates
**Unit Tests**:
- All tools tested independently with mocks
- All channel handlers tested with mocked APIs
- All database queries tested with test database
- Minimum 80% code coverage

**Integration Tests**:
- Each channel tested end-to-end
- Cross-channel customer identification tested
- Kafka event flow validated
- Web form submission → agent response → delivery

**Chaos Tests**:
- Random pod kills every 2 hours
- Verify zero message loss
- Verify worker autoscaling
- Verify graceful degradation

**24-Hour Continuous Operation Test** (FINAL CHALLENGE):
- Web Form: 100+ submissions
- Email: 50+ messages processed
- WhatsApp: 50+ messages processed
- Cross-Channel: 10+ customers using multiple channels
- Uptime > 99.9%
- P95 latency < 3 seconds (all channels)
- Escalation rate < 25%
- Cross-channel ID accuracy > 95%
- Zero message loss

## Technical Standards

### Performance Targets
- **Response Time**: < 3 seconds (processing)
- **Delivery Time**: < 30 seconds (total)
- **Accuracy**: > 85% on test dataset
- **Escalation Rate**: < 20%
- **Uptime**: > 99.9%
- **Cross-Channel ID**: > 95% accuracy

### Technology Stack
- **AI Agent**: OpenAI Agents SDK with GPT-4o
- **Database/CRM**: PostgreSQL 16 with pgvector extension
- **Event Streaming**: Apache Kafka (Confluent Cloud recommended)
- **API Layer**: FastAPI with async/await
- **Web Form**: React with Next.js (REQUIRED deliverable)
- **Email**: Gmail API with Pub/Sub
- **WhatsApp**: Twilio WhatsApp API
- **Deployment**: Kubernetes with HorizontalPodAutoscaler
- **Development**: Claude Code for incubation, OpenAI Agents SDK for production

### Code Quality
- **Type Safety**: All functions fully typed, Pydantic models for all inputs
- **Error Handling**: Every external call wrapped in try/catch with graceful fallbacks
- **Logging**: Structured logging with context (conversation_id, customer_id, channel)
- **No Hardcoded Values**: All config in environment variables or ConfigMaps
- **Idempotency**: All operations safe to retry (using channel_message_id for deduplication)

## Deliverables Checklist

### Stage 1: Incubation
- [ ] Working prototype handling queries from any channel
- [ ] specs/discovery-log.md documenting requirements discovered
- [ ] specs/customer-success-fte-spec.md crystallized specification
- [ ] MCP server with 5+ tools (including channel-aware tools)
- [ ] Agent skills manifest
- [ ] Channel-specific response templates
- [ ] Test dataset with 20+ edge cases per channel
- [ ] Performance baseline measured

### Stage 2: Specialization
- [ ] PostgreSQL schema with multi-channel support (database/schema.sql)
- [ ] OpenAI Agents SDK implementation (agent/customer_success_agent.py)
- [ ] FastAPI service with all endpoints (api/main.py)
- [ ] Gmail integration (channels/gmail_handler.py)
- [ ] WhatsApp integration (channels/whatsapp_handler.py)
- [ ] **Web Support Form** (web-form/SupportForm.jsx) - **REQUIRED**
- [ ] Kafka event streaming (kafka_client.py with topics)
- [ ] Unified message processor (workers/message_processor.py)
- [ ] Kubernetes manifests (k8s/*.yaml)
- [ ] Docker compose for local development

### Stage 3: Integration
- [ ] Multi-channel E2E test suite passing
- [ ] Load test results (100+ concurrent users)
- [ ] 24-hour continuous operation test passed
- [ ] Documentation (README, API docs, deployment guide)
- [ ] Runbook for incident response

## Non-Negotiables

1. **Web Support Form is MANDATORY** - Complete React/Next.js component with validation
2. **PostgreSQL IS the CRM** - No external CRM integration required
3. **All Three Channels** - Gmail, WhatsApp, and Web Form must work
4. **24/7 Operation** - Must pass chaos testing and 24-hour test
5. **Zero Message Loss** - Kafka guarantees delivery
6. **Cross-Channel Continuity** - Customer history preserved across channels
7. **Production-Grade** - This is a real deployable system, not a demo

## What We're NOT Building
- ❌ Full website (only the support form component)
- ❌ External CRM integration (PostgreSQL is sufficient)
- ❌ Production WhatsApp Business account (Twilio sandbox OK)
- ❌ Human agent dashboard (out of scope)
- ❌ Billing system (only escalate billing questions)
- ❌ Multi-language support (English only)
- ❌ Mobile app (web form is embeddable)

## Success Metrics

### Cost Efficiency
- Human FTE cost: $75,000/year + benefits + overhead
- Digital FTE target: < $1,000/year
- Cost per interaction: < $0.10

### Operational Metrics
- Uptime: > 99.9%
- P95 Latency: < 3 seconds (all channels)
- Escalation Rate: < 25%
- Message Loss: 0%
- Cross-Channel ID Accuracy: > 95%

### Business Metrics
- Customer Satisfaction: > 4.0/5.0
- First Response Time: < 5 minutes
- Resolution Rate: > 75%
- 24/7 availability (no human required)

## Governance
- This constitution guides ALL implementation decisions
- When in doubt, refer to these principles
- Changes to constitution require documented justification
- All code reviews must verify compliance with principles
- Performance metrics must be tracked and reported

**Version**: 1.0.0 | **Ratified**: 2026-03-14 | **Last Amended**: 2026-03-14
