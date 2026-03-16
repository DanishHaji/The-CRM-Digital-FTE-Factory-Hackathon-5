"""
Digital FTE Customer Success Agent - Knowledge Base Seeding
Populate knowledge_base table with sample product documentation
"""

import asyncio
from uuid import uuid4

from .connection import get_connection
from ..utils.logger import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)


# Sample product documentation for knowledge base
SAMPLE_KNOWLEDGE_BASE = [
    {
        "title": "Product Overview - Digital FTE Customer Success Agent",
        "content": "The Digital FTE Customer Success Agent is an AI-powered 24/7 autonomous customer support system that handles inquiries across three channels: Gmail (email), WhatsApp (messaging), and Web Form (website). It provides intelligent responses using OpenAI GPT-4o, maintains cross-channel customer history, and escalates complex issues to human agents when necessary.",
        "category": "Product Information",
        "source_url": "https://docs.example.com/product-overview"
    },
    {
        "title": "Multi-Channel Support - How It Works",
        "content": "Customers can reach support via three channels: 1) Email to support@company.com using Gmail API, 2) WhatsApp messaging via Twilio integration, 3) Web Support Form on the company website. All channels are processed by the same AI agent, and customer history is preserved across channels using email as the primary identifier.",
        "category": "Features",
        "source_url": "https://docs.example.com/multi-channel"
    },
    {
        "title": "Cross-Channel Customer Identification",
        "content": "The system maintains > 95% accuracy in identifying the same customer across different channels. Email is the primary identifier, while phone numbers are linked via the customer_identifiers table. When a customer who previously emailed contacts via WhatsApp, the system retrieves their complete conversation history from all channels.",
        "category": "Features",
        "source_url": "https://docs.example.com/cross-channel"
    },
    {
        "title": "Response Time and Performance",
        "content": "The Digital FTE processes customer requests in < 3 seconds (P95 latency) and delivers complete responses within 30 seconds total. The system maintains > 99.9% uptime and scales automatically from 3 to 20 API pods and 3 to 30 worker pods based on load.",
        "category": "Performance",
        "source_url": "https://docs.example.com/performance"
    },
    {
        "title": "Escalation to Human Agents",
        "content": "The system automatically escalates to human support when: customer mentions legal keywords (lawyer, sue, attorney), sentiment score < 0.3 (angry/frustrated), knowledge base search fails after 2 attempts, customer explicitly requests human help, or customer asks about pricing or refunds. Escalation rate target is < 25%.",
        "category": "Features",
        "source_url": "https://docs.example.com/escalation"
    },
    {
        "title": "Pricing Information",
        "content": "For pricing questions, please contact our sales team directly. The Digital FTE will escalate pricing inquiries to a human representative who can provide detailed pricing information based on your specific needs.",
        "category": "Pricing",
        "source_url": "https://www.example.com/pricing"
    },
    {
        "title": "Refund Policy",
        "content": "Refund requests are handled by our billing department. Please contact billing@company.com or request to speak with a human agent for refund inquiries. Processing time for refunds is typically 5-7 business days.",
        "category": "Billing",
        "source_url": "https://docs.example.com/refund-policy"
    },
    {
        "title": "Getting Started with Web Support Form",
        "content": "To submit a support request via the Web Form: 1) Visit support.company.com, 2) Fill in your name, email, and message, 3) Click Submit. You'll receive a confirmation email immediately and a response from our Digital FTE within minutes. You can check the status of your request using the provided ticket ID.",
        "category": "How-To",
        "source_url": "https://docs.example.com/web-form-guide"
    },
    {
        "title": "How to Contact Support via Email",
        "content": "Send an email to support@company.com with your question or issue. Include relevant details such as account information, error messages, or screenshots. Our Digital FTE will respond with a formal, detailed email within minutes. Email responses are formatted with a greeting, detailed explanation, and professional signature.",
        "category": "How-To",
        "source_url": "https://docs.example.com/email-support"
    },
    {
        "title": "WhatsApp Support - Quick Help",
        "content": "For instant messaging support, send a WhatsApp message to our support number. Responses are concise (< 300 characters) and conversational. If you need to speak with a human agent, simply send the message 'human', 'agent', or 'representative'.",
        "category": "How-To",
        "source_url": "https://docs.example.com/whatsapp-support"
    },
    {
        "title": "Account Setup and Configuration",
        "content": "To set up your account: 1) Verify your email address, 2) Complete your profile information, 3) Set up two-factor authentication (recommended), 4) Configure notification preferences. For assistance with account setup, contact support via any channel.",
        "category": "Account Management",
        "source_url": "https://docs.example.com/account-setup"
    },
    {
        "title": "Troubleshooting Login Issues",
        "content": "If you're having trouble logging in: 1) Verify you're using the correct email address, 2) Try resetting your password, 3) Clear browser cache and cookies, 4) Disable browser extensions, 5) Try a different browser. If the issue persists, contact support with details about the error message you're seeing.",
        "category": "Troubleshooting",
        "source_url": "https://docs.example.com/login-troubleshooting"
    },
    {
        "title": "Data Privacy and Security",
        "content": "We take your privacy seriously. All customer data is stored securely in PostgreSQL with encryption at rest. We support GDPR data export and deletion requests. For privacy-related questions, contact privacy@company.com or request human escalation.",
        "category": "Privacy & Security",
        "source_url": "https://docs.example.com/privacy"
    },
    {
        "title": "System Status and Uptime",
        "content": "Our Digital FTE operates 24/7 with > 99.9% uptime guarantee. Check status.company.com for real-time system status. We use Kubernetes autoscaling and chaos engineering to ensure continuous operation even during infrastructure failures.",
        "category": "System Information",
        "source_url": "https://status.example.com"
    },
    {
        "title": "API Integration Documentation",
        "content": "For developers integrating with our API: We provide REST APIs for ticket submission, status checking, and webhook notifications. API documentation is available at docs.example.com/api. For API keys and authentication, contact api-support@company.com.",
        "category": "Developer",
        "source_url": "https://docs.example.com/api"
    }
]


async def seed_knowledge_base():
    """Seed the knowledge_base table with sample documentation."""
    logger.info("Starting knowledge base seeding...")

    async with get_connection() as conn:
        # Clear existing entries (for development only!)
        await conn.execute("DELETE FROM knowledge_base")
        logger.info("Cleared existing knowledge base entries")

        # Insert sample entries (without embeddings - those are generated separately)
        for entry in SAMPLE_KNOWLEDGE_BASE:
            await conn.execute("""
                INSERT INTO knowledge_base (entry_id, title, content, category, source_url)
                VALUES ($1, $2, $3, $4, $5)
            """, uuid4(), entry["title"], entry["content"], entry["category"], entry["source_url"])

        logger.info(f"Inserted {len(SAMPLE_KNOWLEDGE_BASE)} knowledge base entries")

    logger.info("Knowledge base seeding completed successfully!")


if __name__ == "__main__":
    asyncio.run(seed_knowledge_base())
