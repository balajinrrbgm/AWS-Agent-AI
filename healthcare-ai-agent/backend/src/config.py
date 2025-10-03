"""
Configuration settings for the Healthcare AI Agent Backend

This module contains all configuration settings for the application,
including AWS service configurations, database settings, and security parameters.
"""

import os
from typing import Optional, List
from pydantic import BaseSettings, validator
import secrets

class Settings(BaseSettings):
    """
    Application settings and configuration
    """
    
    # Application settings
    app_name: str = "Healthcare AI Agent"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = False
    
    # Security settings
    secret_key: str = secrets.token_urlsafe(32)
    access_token_expire_minutes: int = 1440  # 24 hours
    algorithm: str = "HS256"
    
    # AWS settings
    aws_region: str = "us-east-1"
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    
    # Bedrock settings
    bedrock_region: str = "us-east-1"
    bedrock_model_id: str = "anthropic.claude-3-sonnet-20240229-v1:0"
    bedrock_max_tokens: int = 4000
    bedrock_temperature: float = 0.1
    
    # SageMaker settings
    sagemaker_region: str = "us-east-1"
    sagemaker_endpoint_name: Optional[str] = None
    sagemaker_model_name: str = "healthcare-symptom-analyzer"
    
    # DynamoDB settings
    dynamodb_region: str = "us-east-1"
    patients_table_name: str = "healthcare-patients"
    appointments_table_name: str = "healthcare-appointments"
    sessions_table_name: str = "healthcare-sessions"
    
    # S3 settings
    s3_region: str = "us-east-1"
    s3_bucket_name: str = "healthcare-ai-documents"
    
    # Cognito settings
    cognito_region: str = "us-east-1"
    cognito_user_pool_id: Optional[str] = None
    cognito_client_id: Optional[str] = None
    
    # API Gateway settings
    api_gateway_stage: str = "dev"
    api_gateway_url: Optional[str] = None
    
    # Lambda settings
    lambda_region: str = "us-east-1"
    
    # CloudWatch settings
    cloudwatch_log_group: str = "/aws/lambda/healthcare-ai-agent"
    
    # CORS settings
    cors_origins: List[str] = [
        "http://localhost:3000",
        "http://localhost:8080",
        "https://localhost:3000",
        "https://localhost:8080"
    ]
    cors_allow_credentials: bool = True
    cors_allow_methods: List[str] = ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"]
    cors_allow_headers: List[str] = ["*"]
    
    # Rate limiting
    rate_limit_requests: int = 100
    rate_limit_period: int = 3600  # 1 hour
    
    # Logging settings
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Database settings (for local development)
    database_url: str = "sqlite:///./healthcare_ai.db"
    database_echo: bool = False
    
    # Redis settings (for caching and sessions)
    redis_url: str = "redis://localhost:6379/0"
    redis_expire_time: int = 3600  # 1 hour
    
    # Email settings (for notifications)
    smtp_server: Optional[str] = None
    smtp_port: int = 587
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    
    # Webhook settings
    webhook_secret: Optional[str] = None
    webhook_timeout: int = 30
    
    # Development/Testing flags
    use_mock_aws_services: bool = True  # Set to False in production
    enable_api_docs: bool = True
    enable_metrics: bool = True
    
    @validator('cors_origins', pre=True)
    def assemble_cors_origins(cls, v):
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v
    
    @validator('debug', pre=True)
    def parse_debug(cls, v):
        if isinstance(v, str):
            return v.lower() in ('true', '1', 'yes', 'on')
        return v
    
    @validator('use_mock_aws_services', pre=True)
    def parse_mock_services(cls, v):
        if isinstance(v, str):
            return v.lower() in ('true', '1', 'yes', 'on')
        return v
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        
        # Environment variable prefixes
        env_prefix = "HEALTHCARE_AI_"
        
        # Field aliases for common environment variables
        fields = {
            'aws_access_key_id': {'env': ['AWS_ACCESS_KEY_ID', 'HEALTHCARE_AI_AWS_ACCESS_KEY_ID']},
            'aws_secret_access_key': {'env': ['AWS_SECRET_ACCESS_KEY', 'HEALTHCARE_AI_AWS_SECRET_ACCESS_KEY']},
            'secret_key': {'env': ['SECRET_KEY', 'HEALTHCARE_AI_SECRET_KEY']},
            'database_url': {'env': ['DATABASE_URL', 'HEALTHCARE_AI_DATABASE_URL']},
            'redis_url': {'env': ['REDIS_URL', 'HEALTHCARE_AI_REDIS_URL']},
        }

class DevelopmentSettings(Settings):
    """
    Development-specific settings
    """
    debug: bool = True
    reload: bool = True
    use_mock_aws_services: bool = True
    log_level: str = "DEBUG"
    
    # Local development AWS settings
    aws_region: str = "us-east-1"
    bedrock_region: str = "us-east-1"
    
    # Allow more permissive CORS for development
    cors_origins: List[str] = ["*"]

class ProductionSettings(Settings):
    """
    Production-specific settings
    """
    debug: bool = False
    reload: bool = False
    use_mock_aws_services: bool = False
    log_level: str = "INFO"
    
    # Stricter CORS for production
    cors_origins: List[str] = [
        "https://yourdomain.com",
        "https://www.yourdomain.com"
    ]

class TestingSettings(Settings):
    """
    Testing-specific settings
    """
    debug: bool = True
    use_mock_aws_services: bool = True
    database_url: str = "sqlite:///./test_healthcare_ai.db"
    
    # Test-specific table names
    patients_table_name: str = "test-healthcare-patients"
    appointments_table_name: str = "test-healthcare-appointments"
    sessions_table_name: str = "test-healthcare-sessions"

def get_settings() -> Settings:
    """
    Get settings based on environment
    """
    environment = os.getenv("ENVIRONMENT", "development").lower()
    
    if environment == "production":
        return ProductionSettings()
    elif environment == "testing":
        return TestingSettings()
    else:
        return DevelopmentSettings()

# Global settings instance
settings = get_settings()

# Export commonly used settings
AWS_REGION = settings.aws_region
BEDROCK_MODEL_ID = settings.bedrock_model_id
USE_MOCK_SERVICES = settings.use_mock_aws_services
SECRET_KEY = settings.secret_key
CORS_ORIGINS = settings.cors_origins