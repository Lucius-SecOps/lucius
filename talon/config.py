"""Talon configuration management."""

import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class DatabaseConfig:
    """Database configuration."""
    
    url: str = field(
        default_factory=lambda: os.getenv(
            "DATABASE_URL",
            "postgresql://lucius:lucius_secret@localhost:5432/lucius_db"
        )
    )
    pool_size: int = 10
    pool_recycle: int = 3600
    echo: bool = field(default_factory=lambda: os.getenv("FLASK_ENV") == "development")


@dataclass
class RedisConfig:
    """Redis configuration."""
    
    url: str = field(
        default_factory=lambda: os.getenv("REDIS_URL", "redis://localhost:6379/0")
    )
    ttl: int = 3600


@dataclass
class CeleryConfig:
    """Celery configuration."""
    
    broker_url: str = field(
        default_factory=lambda: os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1")
    )
    result_backend: str = field(
        default_factory=lambda: os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/2")
    )
    task_serializer: str = "json"
    result_serializer: str = "json"
    accept_content: list = field(default_factory=lambda: ["json"])
    timezone: str = "UTC"
    enable_utc: bool = True
    task_track_started: bool = True
    task_time_limit: int = 3600
    worker_prefetch_multiplier: int = 1


@dataclass
class TwilioConfig:
    """Twilio SMS configuration."""
    
    account_sid: Optional[str] = field(
        default_factory=lambda: os.getenv("TWILIO_ACCOUNT_SID")
    )
    auth_token: Optional[str] = field(
        default_factory=lambda: os.getenv("TWILIO_AUTH_TOKEN")
    )
    from_number: Optional[str] = field(
        default_factory=lambda: os.getenv("TWILIO_FROM_NUMBER")
    )
    
    @property
    def is_configured(self) -> bool:
        return all([self.account_sid, self.auth_token, self.from_number])


@dataclass
class SendGridConfig:
    """SendGrid email configuration."""
    
    api_key: Optional[str] = field(
        default_factory=lambda: os.getenv("SENDGRID_API_KEY")
    )
    from_email: str = field(
        default_factory=lambda: os.getenv("SENDGRID_FROM_EMAIL", "alerts@lucius.io")
    )
    
    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)


@dataclass
class SlackConfig:
    """Slack notification configuration."""
    
    webhook_url: Optional[str] = field(
        default_factory=lambda: os.getenv("SLACK_WEBHOOK_URL")
    )
    
    @property
    def is_configured(self) -> bool:
        return bool(self.webhook_url)


@dataclass
class Config:
    """Main configuration container."""
    
    # Flask
    secret_key: str = field(
        default_factory=lambda: os.getenv("SECRET_KEY", "change-me-in-production")
    )
    debug: bool = field(
        default_factory=lambda: os.getenv("FLASK_ENV") == "development"
    )
    
    # Services
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    redis: RedisConfig = field(default_factory=RedisConfig)
    celery: CeleryConfig = field(default_factory=CeleryConfig)
    
    # Notifications
    twilio: TwilioConfig = field(default_factory=TwilioConfig)
    sendgrid: SendGridConfig = field(default_factory=SendGridConfig)
    slack: SlackConfig = field(default_factory=SlackConfig)
    
    # Logging
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    
    @classmethod
    def from_env(cls) -> "Config":
        """Create configuration from environment variables."""
        return cls()


# Global configuration instance
config = Config.from_env()
