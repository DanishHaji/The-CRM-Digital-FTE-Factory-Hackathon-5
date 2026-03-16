"""
Digital FTE Customer Success Agent - Configuration Management
Environment configuration using Pydantic Settings
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
from functools import lru_cache


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    # Database Configuration
    database_url: str = "postgresql://postgres:postgres@localhost:5432/digital_fte"
    database_host: str = "localhost"
    database_port: int = 5432
    database_name: str = "digital_fte"
    database_user: str = "postgres"
    database_password: str = "postgres"
    database_max_connections: int = 20

    # Kafka Configuration
    kafka_broker: str = "localhost:9092"
    kafka_consumer_group: str = "digital-fte-workers"
    kafka_topic_incoming: str = "fte.tickets.incoming"
    kafka_topic_gmail: str = "fte.tickets.gmail"
    kafka_topic_whatsapp: str = "fte.tickets.whatsapp"
    kafka_topic_web: str = "fte.tickets.web"

    # AI Provider Configuration
    ai_provider: str = "groq"  # Options: "openai" or "groq"

    # Groq API (Free & Fast)
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"

    # OpenAI API (Optional)
    openai_api_key: str = "sk-test"
    openai_model: str = "gpt-4o"
    openai_embedding_model: str = "text-embedding-3-small"

    # Gmail API Configuration
    gmail_credentials_file: str = "credentials/gmail_credentials.json"
    gmail_token_file: str = "credentials/gmail_token.json"
    gmail_pubsub_topic: str = ""
    gmail_pubsub_subscription: str = ""
    support_email: str = "support@yourcompany.com"

    # Twilio WhatsApp Configuration
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_whatsapp_from: str = "whatsapp:+14155238886"
    twilio_webhook_validate: bool = True

    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 4
    api_key: str = "dev_api_key_change_in_production"

    # CORS Configuration
    cors_origins: str = "http://localhost:3000,https://yourcompany.com"
    cors_allow_credentials: bool = True

    # Logging Configuration
    log_level: str = "INFO"
    log_format: str = "json"
    log_file: str = "logs/digital-fte.log"

    # Channel Configuration
    channel_email_max_response_length: int = 500
    channel_whatsapp_max_response_length: int = 300
    channel_web_max_response_length: int = 300
    channel_whatsapp_split_threshold: int = 1600

    # Agent Configuration
    agent_max_search_attempts: int = 2
    agent_sentiment_threshold: float = 0.3
    agent_escalation_keywords: str = "lawyer,legal,sue,attorney"

    # Environment
    environment: str = "development"
    replica_count: int = 3

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def escalation_keywords_list(self) -> List[str]:
        """Parse escalation keywords from comma-separated string."""
        return [kw.strip().lower() for kw in self.agent_escalation_keywords.split(",")]

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment.lower() == "development"


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    Using lru_cache ensures settings are loaded only once.

    Returns:
        Settings: Application settings
    """
    return Settings()
