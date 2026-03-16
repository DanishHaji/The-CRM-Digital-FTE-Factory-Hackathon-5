-- Digital FTE Customer Success Agent - PostgreSQL Database Schema
-- PostgreSQL 16 with pgvector extension
-- This database serves as the complete CRM system (no external CRM needed)

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;

-- Drop existing tables if they exist (for fresh installation)
DROP TABLE IF EXISTS agent_metrics CASCADE;
DROP TABLE IF EXISTS channel_configs CASCADE;
DROP TABLE IF EXISTS knowledge_base CASCADE;
DROP TABLE IF EXISTS tickets CASCADE;
DROP TABLE IF EXISTS messages CASCADE;
DROP TABLE IF EXISTS conversations CASCADE;
DROP TABLE IF EXISTS customer_identifiers CASCADE;
DROP TABLE IF EXISTS customers CASCADE;

-- =============================================================================
-- CUSTOMERS: Unified customer records across all channels
-- =============================================================================
CREATE TABLE customers (
    customer_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,  -- Primary identifier across all channels
    name VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'  -- Channel-specific data (phone, preferences, etc.)
);

-- Index for fast email lookup
CREATE INDEX idx_customers_email ON customers(email);

-- Trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_customers_updated_at BEFORE UPDATE ON customers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- CUSTOMER_IDENTIFIERS: Cross-channel identity linking
-- =============================================================================
CREATE TABLE customer_identifiers (
    identifier_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id UUID NOT NULL REFERENCES customers(customer_id) ON DELETE CASCADE,
    identifier_type VARCHAR(50) NOT NULL,  -- 'email', 'phone', 'whatsapp_id'
    identifier_value VARCHAR(255) NOT NULL,
    verified BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(identifier_type, identifier_value)
);

-- Indexes for fast customer lookup by identifier
CREATE INDEX idx_customer_identifiers_customer_id ON customer_identifiers(customer_id);
CREATE INDEX idx_customer_identifiers_type_value ON customer_identifiers(identifier_type, identifier_value);

-- =============================================================================
-- CONVERSATIONS: Interaction sessions with customers
-- =============================================================================
CREATE TABLE conversations (
    conversation_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id UUID NOT NULL REFERENCES customers(customer_id) ON DELETE CASCADE,
    initial_channel VARCHAR(50) NOT NULL,  -- 'email', 'whatsapp', 'web'
    status VARCHAR(50) DEFAULT 'open',  -- 'open', 'resolved', 'escalated'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for conversation queries
CREATE INDEX idx_conversations_customer_id ON conversations(customer_id);
CREATE INDEX idx_conversations_status ON conversations(status);

CREATE TRIGGER update_conversations_updated_at BEFORE UPDATE ON conversations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- MESSAGES: All messages with channel, direction, role tracking
-- =============================================================================
CREATE TABLE messages (
    message_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID NOT NULL REFERENCES conversations(conversation_id) ON DELETE CASCADE,
    channel VARCHAR(50) NOT NULL,  -- 'email', 'whatsapp', 'web'
    direction VARCHAR(50) NOT NULL,  -- 'inbound', 'outbound'
    role VARCHAR(50) NOT NULL,  -- 'user', 'assistant'
    content TEXT NOT NULL,
    channel_message_id VARCHAR(255),  -- Gmail message_id, Twilio SID, web submission_id
    metadata JSONB DEFAULT '{}',  -- Channel-specific data (headers, sender info, etc.)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(channel, channel_message_id)  -- Prevent duplicate processing
);

-- Indexes for message queries
CREATE INDEX idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX idx_messages_channel ON messages(channel);
CREATE INDEX idx_messages_channel_message_id ON messages(channel, channel_message_id);
CREATE INDEX idx_messages_created_at ON messages(created_at DESC);

-- =============================================================================
-- TICKETS: Support tickets with source_channel tracking
-- =============================================================================
CREATE TABLE tickets (
    ticket_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID NOT NULL REFERENCES conversations(conversation_id) ON DELETE CASCADE,
    source_channel VARCHAR(50) NOT NULL,  -- 'email', 'whatsapp', 'web'
    priority VARCHAR(50) DEFAULT 'medium',  -- 'low', 'medium', 'high', 'urgent'
    status VARCHAR(50) DEFAULT 'pending',  -- 'pending', 'processing', 'responded', 'escalated'
    assigned_to UUID,  -- NULL for Digital FTE, user_id for human escalation
    escalation_reason TEXT,  -- Reason for escalation if status='escalated'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP
);

-- Indexes for ticket queries
CREATE INDEX idx_tickets_conversation_id ON tickets(conversation_id);
CREATE INDEX idx_tickets_status ON tickets(status);
CREATE INDEX idx_tickets_source_channel ON tickets(source_channel);
CREATE INDEX idx_tickets_assigned_to ON tickets(assigned_to);

CREATE TRIGGER update_tickets_updated_at BEFORE UPDATE ON tickets
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- KNOWLEDGE_BASE: Product documentation with pgvector embeddings
-- =============================================================================
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

-- Index for fast vector similarity search using ivfflat
CREATE INDEX idx_knowledge_base_embedding ON knowledge_base
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Index for category filtering
CREATE INDEX idx_knowledge_base_category ON knowledge_base(category);

CREATE TRIGGER update_knowledge_base_updated_at BEFORE UPDATE ON knowledge_base
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- CHANNEL_CONFIGS: Per-channel configuration
-- =============================================================================
CREATE TABLE channel_configs (
    config_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    channel_name VARCHAR(50) UNIQUE NOT NULL,  -- 'email', 'whatsapp', 'web'
    enabled BOOLEAN DEFAULT true,
    config_json JSONB NOT NULL,  -- API keys, formatting rules, rate limits
    max_response_length INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TRIGGER update_channel_configs_updated_at BEFORE UPDATE ON channel_configs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- AGENT_METRICS: Performance tracking by channel
-- =============================================================================
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

-- Indexes for metrics queries
CREATE INDEX idx_agent_metrics_channel ON agent_metrics(channel);
CREATE INDEX idx_agent_metrics_ticket_id ON agent_metrics(ticket_id);
CREATE INDEX idx_agent_metrics_created_at ON agent_metrics(created_at DESC);
CREATE INDEX idx_agent_metrics_escalation ON agent_metrics(escalation);

-- =============================================================================
-- SEED DATA: Initial channel configurations
-- =============================================================================

-- Email channel configuration
INSERT INTO channel_configs (channel_name, enabled, config_json, max_response_length)
VALUES (
    'email',
    true,
    '{
        "tone": "formal",
        "include_greeting": true,
        "include_signature": true,
        "signature": "Best regards,\nCustomer Success Team",
        "max_words": 500
    }'::jsonb,
    500
);

-- WhatsApp channel configuration
INSERT INTO channel_configs (channel_name, enabled, config_json, max_response_length)
VALUES (
    'whatsapp',
    true,
    '{
        "tone": "conversational",
        "include_greeting": false,
        "split_threshold": 1600,
        "preferred_length": 300
    }'::jsonb,
    300
);

-- Web Form channel configuration
INSERT INTO channel_configs (channel_name, enabled, config_json, max_response_length)
VALUES (
    'web',
    true,
    '{
        "tone": "semi-formal",
        "send_email_notification": true,
        "max_words": 300
    }'::jsonb,
    300
);

-- =============================================================================
-- VIEWS: Useful queries for analytics
-- =============================================================================

-- View: Customer complete profile with all identifiers
CREATE VIEW customer_profiles AS
SELECT
    c.customer_id,
    c.email,
    c.name,
    c.created_at,
    c.updated_at,
    json_agg(
        json_build_object(
            'type', ci.identifier_type,
            'value', ci.identifier_value,
            'verified', ci.verified
        )
    ) FILTER (WHERE ci.identifier_id IS NOT NULL) AS identifiers
FROM customers c
LEFT JOIN customer_identifiers ci ON c.customer_id = ci.customer_id
GROUP BY c.customer_id, c.email, c.name, c.created_at, c.updated_at;

-- View: Ticket summary with customer and conversation info
CREATE VIEW ticket_summary AS
SELECT
    t.ticket_id,
    t.status,
    t.priority,
    t.source_channel,
    t.created_at,
    t.resolved_at,
    c.email AS customer_email,
    c.name AS customer_name,
    conv.initial_channel,
    COUNT(m.message_id) AS message_count
FROM tickets t
JOIN conversations conv ON t.conversation_id = conv.conversation_id
JOIN customers c ON conv.customer_id = c.customer_id
LEFT JOIN messages m ON conv.conversation_id = m.conversation_id
GROUP BY t.ticket_id, t.status, t.priority, t.source_channel, t.created_at,
         t.resolved_at, c.email, c.name, conv.initial_channel;

-- View: Performance metrics by channel
CREATE VIEW channel_performance AS
SELECT
    channel,
    COUNT(*) AS total_interactions,
    AVG(response_time_ms) AS avg_response_time_ms,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY response_time_ms) AS p95_response_time_ms,
    SUM(CASE WHEN escalation THEN 1 ELSE 0 END) AS escalated_count,
    ROUND(100.0 * SUM(CASE WHEN escalation THEN 1 ELSE 0 END) / COUNT(*), 2) AS escalation_rate,
    AVG(sentiment_score) AS avg_sentiment,
    AVG(customer_satisfaction) AS avg_satisfaction
FROM agent_metrics
GROUP BY channel;

-- =============================================================================
-- COMMENTS: Table and column descriptions
-- =============================================================================

COMMENT ON TABLE customers IS 'Unified customer records across all channels. Email is the primary identifier.';
COMMENT ON TABLE customer_identifiers IS 'Cross-channel identity linking (email, phone, whatsapp_id) for >95% matching accuracy.';
COMMENT ON TABLE conversations IS 'Interaction sessions tracking initial_channel and current status.';
COMMENT ON TABLE messages IS 'All messages with channel, direction, role. Includes channel_message_id for deduplication.';
COMMENT ON TABLE tickets IS 'Support tickets with source_channel. NULL assigned_to means Digital FTE is handling it.';
COMMENT ON TABLE knowledge_base IS 'Product documentation with pgvector embeddings for semantic search.';
COMMENT ON TABLE channel_configs IS 'Per-channel configuration for response formatting and rate limits.';
COMMENT ON TABLE agent_metrics IS 'Performance tracking: response time, escalation, sentiment, tool calls.';

-- =============================================================================
-- GRANTS: Set up permissions (adjust as needed for your environment)
-- =============================================================================

-- Grant all privileges to the application user (replace 'digital_fte_user' with your user)
-- CREATE USER digital_fte_user WITH PASSWORD 'your_secure_password';
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO digital_fte_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO digital_fte_user;

-- =============================================================================
-- SCHEMA VALIDATION
-- =============================================================================

-- Verify pgvector extension is loaded
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector') THEN
        RAISE EXCEPTION 'pgvector extension is not installed. Install it with: CREATE EXTENSION vector;';
    END IF;
END $$;

-- Success message
DO $$
BEGIN
    RAISE NOTICE 'Digital FTE database schema created successfully!';
    RAISE NOTICE 'Tables: customers, customer_identifiers, conversations, messages, tickets, knowledge_base, channel_configs, agent_metrics';
    RAISE NOTICE 'Views: customer_profiles, ticket_summary, channel_performance';
    RAISE NOTICE 'Extensions: uuid-ossp, vector (pgvector)';
END $$;
