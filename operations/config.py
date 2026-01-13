"""Operations configuration management."""

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
    pool_size: int = 5
    echo: bool = field(default_factory=lambda: os.getenv("DEBUG", "").lower() == "true")


@dataclass
class TalonConfig:
    """Talon API configuration."""
    
    api_url: str = field(
        default_factory=lambda: os.getenv("TALON_API_URL", "http://localhost:5000")
    )
    api_key: Optional[str] = field(
        default_factory=lambda: os.getenv("TALON_API_KEY")
    )
    timeout: int = 30


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
class SchedulerConfig:
    """Scheduler configuration."""
    
    deadline_check_interval: int = 3600  # 1 hour
    reminder_days_before: list = field(default_factory=lambda: [7, 3, 1])  # Days before deadline


@dataclass
class Config:
    """Main configuration container."""
    
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    talon: TalonConfig = field(default_factory=TalonConfig)
    twilio: TwilioConfig = field(default_factory=TwilioConfig)
    scheduler: SchedulerConfig = field(default_factory=SchedulerConfig)
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    
    @classmethod
    def from_env(cls) -> "Config":
        """Create configuration from environment variables."""
        return cls()


# Global configuration instance
config = Config.from_env()
