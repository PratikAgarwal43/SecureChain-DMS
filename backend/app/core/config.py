import json
from typing import Annotated, Any, Union
from pydantic import BeforeValidator, PostgresDsn, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


def parse_cors(v: Any) -> list[str]:
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",")]
    elif isinstance(v, (list, str)):
        if isinstance(v, str):
            v = json.loads(v)
        return v
    raise ValueError(v)


class Settings(BaseSettings):
    PROJECT_NAME: str = "SecureChain DMS Backend"
    API_V1_STR: str = "/api/v1"

    # Database Configuration
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "securechain_dms"
    DATABASE_URL: Union[str, None] = None

    # Storage Configuration
    STORAGE_PROVIDER: str = "GCS"

    # GCS Storage Configuration
    GCS_BUCKET_NAME: str = "securechain-documents"
    GCS_PROJECT_ID: Union[str, None] = None
    GCS_CREDENTIALS_FILE: Union[str, None] = None

    # MinIO Storage Configuration (Legacy / Fallback)
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_SECURE: bool = False
    MINIO_BUCKET_NAME: str = "securechain-documents"

    # JWT Authentication Configuration
    JWT_SECRET_KEY: str = "securechain_dms_jwt_secret_key_change_in_production_32_bytes_min"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    DEMO_USER_PASSWORD: str = "demo-password"

    # AI-OCR Microservice Configuration
    OCR_SERVICE_URL: str = "http://localhost:8000"
    OCR_SERVICE_TIMEOUT: float = 90.0

    # Quorum Approval Engine Configuration
    QUORUM_SERVICE_URL: str = "http://localhost:3000"
    QUORUM_SERVICE_TIMEOUT: float = 15.0

    # Key Management Configuration
    MASTER_KEK: Union[str, None] = None
    KEK_VERSION: str = "v1"

    # CORS Configuration

    CORS_ORIGINS: Annotated[list[str], BeforeValidator(parse_cors)] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    @computed_field
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )


settings = Settings()
