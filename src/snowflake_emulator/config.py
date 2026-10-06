"""
Configuration module for Snowflake Emulator.
"""

import os
from pydantic import BaseModel, Field


class Settings(BaseModel):
    # Server settings
    host: str = Field(default_factory=lambda: os.getenv("EMULATOR_HOST", "0.0.0.0"))
    port: int = Field(default_factory=lambda: int(os.getenv("EMULATOR_PORT", "8080")))
    
    # Engine settings
    db_path: str = Field(default_factory=lambda: os.getenv("EMULATOR_DB_PATH", ":memory:"))
    
    # Defaults
    default_database: str = Field(default_factory=lambda: os.getenv("DEFAULT_DATABASE", "DEMO_DB"))
    default_schema: str = Field(default_factory=lambda: os.getenv("DEFAULT_SCHEMA", "PUBLIC"))
    default_warehouse: str = Field(default_factory=lambda: os.getenv("DEFAULT_WAREHOUSE", "COMPUTE_WH"))
    default_role: str = Field(default_factory=lambda: os.getenv("DEFAULT_ROLE", "ACCOUNTADMIN"))
    default_user: str = Field(default_factory=lambda: os.getenv("DEFAULT_USER", "ADMIN"))
    
    # Cloud Storage / MinIO settings
    s3_endpoint_url: str = Field(default_factory=lambda: os.getenv("S3_ENDPOINT_URL", "http://localhost:9000"))
    aws_access_key_id: str = Field(default_factory=lambda: os.getenv("AWS_ACCESS_KEY_ID", "minioadmin"))
    aws_secret_access_key: str = Field(default_factory=lambda: os.getenv("AWS_SECRET_ACCESS_KEY", "minioadmin"))
    aws_default_region: str = Field(default_factory=lambda: os.getenv("AWS_DEFAULT_REGION", "us-east-1"))
    
    # Local stage storage directory
    local_stage_dir: str = Field(default_factory=lambda: os.getenv("LOCAL_STAGE_DIR", "./stage_storage"))


settings = Settings()
