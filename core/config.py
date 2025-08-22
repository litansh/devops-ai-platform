"""
Configuration management for DevOps AI Platform.

This module handles all configuration settings using Pydantic for validation
and type safety.
"""

import os
from typing import Optional, List
from pydantic import Field, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with validation."""
    
    # Platform Configuration
    platform_env: str = Field(default="development", env="PLATFORM_ENV")
    debug: bool = Field(default=True, env="DEBUG")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # AWS Configuration
    aws_access_key_id: Optional[str] = Field(default=None, env="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: Optional[str] = Field(default=None, env="AWS_SECRET_ACCESS_KEY")
    aws_region: str = Field(default="us-west-2", env="AWS_REGION")
    aws_default_region: str = Field(default="us-west-2", env="AWS_DEFAULT_REGION")
    
    # GCP Configuration (for future use)
    google_application_credentials: Optional[str] = Field(default=None, env="GOOGLE_APPLICATION_CREDENTIALS")
    gcp_project_id: Optional[str] = Field(default=None, env="GCP_PROJECT_ID")
    
    # Bot Configuration
    telegram_bot_token: Optional[str] = Field(default=None, env="TELEGRAM_BOT_TOKEN")
    slack_bot_token: Optional[str] = Field(default=None, env="SLACK_BOT_TOKEN")
    slack_signing_secret: Optional[str] = Field(default=None, env="SLACK_SIGNING_SECRET")
    
    # Database Configuration
    database_url: str = Field(default="postgresql://user:password@localhost:5432/devops_ai_platform", env="DATABASE_URL")
    redis_url: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    mongodb_url: str = Field(default="mongodb://localhost:27017/devops_ai_platform", env="MONGODB_URL")
    
    # AI/ML Configuration
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")
    model_provider: str = Field(default="openai", env="MODEL_PROVIDER")
    
    # Monitoring Configuration
    prometheus_url: str = Field(default="http://localhost:9090", env="PROMETHEUS_URL")
    grafana_url: str = Field(default="http://localhost:3000", env="GRAFANA_URL")
    grafana_api_key: Optional[str] = Field(default=None, env="GRAFANA_API_KEY")
    elasticsearch_url: str = Field(default="http://localhost:9200", env="ELASTICSEARCH_URL")
    
    # Kubernetes Configuration
    kubeconfig: str = Field(default="~/.kube/config", env="KUBECONFIG")
    k8s_namespace: str = Field(default="devops-ai-platform", env="K8S_NAMESPACE")
    
    # GitHub Configuration
    github_token: Optional[str] = Field(default=None, env="GITHUB_TOKEN")
    github_repo: str = Field(default="your-org/devops-ai-platform", env="GITHUB_REPO")
    github_webhook_secret: Optional[str] = Field(default=None, env="GITHUB_WEBHOOK_SECRET")
    
    # Security Configuration
    secret_key: str = Field(default="your_secret_key_here", env="SECRET_KEY")
    jwt_secret_key: str = Field(default="your_jwt_secret_key", env="JWT_SECRET_KEY")
    encryption_key: str = Field(default="your_encryption_key", env="ENCRYPTION_KEY")
    
    # Cost Management
    aws_cost_alert_threshold: float = Field(default=100.0, env="AWS_COST_ALERT_THRESHOLD")
    gcp_cost_alert_threshold: float = Field(default=100.0, env="GCP_COST_ALERT_THRESHOLD")
    budget_alert_email: str = Field(default="admin@yourcompany.com", env="BUDGET_ALERT_EMAIL")
    
    # Agent Configuration
    agent_execution_interval: int = Field(default=300, env="AGENT_EXECUTION_INTERVAL")
    agent_timeout: int = Field(default=60, env="AGENT_TIMEOUT")
    max_concurrent_agents: int = Field(default=10, env="MAX_CONCURRENT_AGENTS")
    
    # Notification Configuration
    alert_email: str = Field(default="alerts@yourcompany.com", env="ALERT_EMAIL")
    slack_channel: str = Field(default="#devops-alerts", env="SLACK_CHANNEL")
    telegram_chat_id: Optional[str] = Field(default=None, env="TELEGRAM_CHAT_ID")
    
    # Performance Configuration
    max_workers: int = Field(default=4, env="MAX_WORKERS")
    worker_timeout: int = Field(default=30, env="WORKER_TIMEOUT")
    cache_ttl: int = Field(default=300, env="CACHE_TTL")
    
    # Development Configuration
    enable_mock_mode: bool = Field(default=False, env="ENABLE_MOCK_MODE")
    enable_debug_mode: bool = Field(default=True, env="ENABLE_DEBUG_MODE")
    enable_profiling: bool = Field(default=False, env="ENABLE_PROFILING")
    
    @validator("log_level")
    def validate_log_level(cls, v):
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of {valid_levels}")
        return v.upper()
    
    @validator("model_provider")
    def validate_model_provider(cls, v):
        """Validate model provider."""
        valid_providers = ["openai", "anthropic"]
        if v.lower() not in valid_providers:
            raise ValueError(f"Model provider must be one of {valid_providers}")
        return v.lower()
    
    @validator("platform_env")
    def validate_platform_env(cls, v):
        """Validate platform environment."""
        valid_envs = ["development", "staging", "production"]
        if v.lower() not in valid_envs:
            raise ValueError(f"Platform environment must be one of {valid_envs}")
        return v.lower()
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get the global settings instance."""
    return settings


def validate_required_settings() -> List[str]:
    """Validate that all required settings are present."""
    errors = []
    
    # Check for required bot configuration
    if not settings.telegram_bot_token and not settings.slack_bot_token:
        errors.append("Either TELEGRAM_BOT_TOKEN or SLACK_BOT_TOKEN must be set")
    
    # Check for required AI configuration
    if settings.model_provider == "openai" and not settings.openai_api_key:
        errors.append("OPENAI_API_KEY is required when using OpenAI")
    elif settings.model_provider == "anthropic" and not settings.anthropic_api_key:
        errors.append("ANTHROPIC_API_KEY is required when using Anthropic")
    
    # Check for required cloud configuration
    if not settings.aws_access_key_id and not settings.google_application_credentials:
        errors.append("Either AWS credentials or GCP credentials must be configured")
    
    # Check for required GitHub configuration
    if not settings.github_token:
        errors.append("GITHUB_TOKEN is required for PR-based workflows")
    
    return errors
