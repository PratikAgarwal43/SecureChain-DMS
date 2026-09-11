"""
config.py — Centralised settings for the API Gateway.
Reads all values from environment variables / .env file.
"""
import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    # --- Database ---
    database_url: str = "postgresql://postgres:1234@localhost:5432/securechain_db"

    # --- JWT ---
    jwt_secret_key: str = "securechain-sih26190-super-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_hours: int = 8
    jwt_refresh_token_expire_days: int = 7

    # --- Downstream Services ---
    ocr_service_url: str = "http://localhost:8001"
    quorum_service_url: str = "http://localhost:3000"

    # --- Cloudflare R2 ---
    r2_account_id: str = ""
    r2_access_key_id: str = ""
    r2_secret_access_key: str = ""
    r2_bucket_name: str = "securechain-vault2"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
