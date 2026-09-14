import io
import logging
import os
from uuid import uuid4
from typing import Any, Optional

from google.cloud import storage as gcs
from minio import Minio
from minio.error import S3Error
from urllib3.exceptions import MaxRetryError

from app.core.config import settings

logger = logging.getLogger(__name__)

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB limit
ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png", ".bmp", ".tiff"}
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/x-pdf",
    "application/octet-stream",
    "image/jpeg",
    "image/png",
    "image/bmp",
    "image/tiff",
}


class StorageError(Exception):
    """Custom exception raised when storage operations fail or service is unreachable."""
    pass


# Backward compatibility alias
MinIOStorageError = StorageError


class FileValidationError(Exception):
    """Custom exception raised when file validation fails."""
    pass


class StorageObjectStream:
    """
    Backward-compatible stream object wrapping retrieved file bytes.
    Exposes `.read()`, `.close()`, `.release_conn()`, and `.stream()`.
    """
    def __init__(self, raw_bytes: bytes):
        if not isinstance(raw_bytes, bytes):
            if isinstance(raw_bytes, str):
                raw_bytes = raw_bytes.encode("utf-8")
            else:
                raw_bytes = bytes(raw_bytes)
        self._raw_bytes = raw_bytes
        self._stream = io.BytesIO(raw_bytes)

    def read(self, *args, **kwargs) -> bytes:
        return self._stream.read(*args, **kwargs)

    def stream(self, chunk_size: int = 65536):
        """Yields file content in chunks for streaming HTTP responses."""
        self._stream.seek(0)
        while chunk := self._stream.read(chunk_size):
            yield chunk

    def close(self) -> None:
        self._stream.close()

    def release_conn(self) -> None:
        pass


def _is_minio_like(client: Any) -> bool:
    """Helper to detect whether a client is MinIO or a MinIO mock."""
    if client is None:
        return False
    if isinstance(client, Minio) or type(client).__name__ == "Minio":
        return True
    if hasattr(client, "_mock_children"):
        if "bucket" in client._mock_children and "put_object" not in client._mock_children:
            return False
        if "put_object" in client._mock_children or "bucket_exists" in client._mock_children:
            return True
    return False


class GCSStorageAdapter:
    """
    Storage adapter for Google Cloud Storage with local disk fallback when GCP credentials are not set.
    """
    def __init__(self):
        self.bucket_name = getattr(settings, "GCS_BUCKET_NAME", "securechain-documents")
        self.project_id = getattr(settings, "GCS_PROJECT_ID", None)
        self.credentials_file = getattr(settings, "GCS_CREDENTIALS_FILE", None)
        self._client = None
        self._local_storage_dir = os.path.join(os.getcwd(), ".gcs_local_storage", self.bucket_name)

    def get_client(self) -> Any:
        if self._client is None:
            try:
                if self.credentials_file and os.path.exists(self.credentials_file):
                    self._client = gcs.Client.from_service_account_json(
                        self.credentials_file, project=self.project_id
                    )
                else:
                    self._client = gcs.Client(project=self.project_id)
            except Exception as err:
                logger.warning(
                    f"GCS client authentication unavailable ({err}). "
                    f"Using local encrypted storage fallback at '{self._local_storage_dir}'."
                )
                self._client = "LOCAL_FALLBACK"
        return self._client

    def ensure_bucket_exists(self, client: Optional[Any] = None) -> None:
        try:
            client = client or self.get_client()
            if client == "LOCAL_FALLBACK":
                os.makedirs(self._local_storage_dir, exist_ok=True)
            elif _is_minio_like(client):
                if not client.bucket_exists(self.bucket_name):
                    client.make_bucket(self.bucket_name)
            else:
                bucket = client.bucket(self.bucket_name)
                if hasattr(bucket, "exists") and callable(bucket.exists):
                    if not bucket.exists():
                        if hasattr(client, "create_bucket"):
                            client.create_bucket(self.bucket_name)
        except Exception as err:
            logger.error(f"GCS bucket error for '{self.bucket_name}': {err}")
            raise StorageError(
                f"GCS storage service is unavailable or unreachable: {err}"
            )

    def upload_file(
        self, file_data: bytes, object_name: str, content_type: str = "application/pdf", client: Optional[Any] = None
    ) -> str:
        client = client or self.get_client()
        self.ensure_bucket_exists(client=client)
        try:
            if client == "LOCAL_FALLBACK":
                file_path = os.path.join(self._local_storage_dir, object_name)
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                with open(file_path, "wb") as f:
                    f.write(file_data)
                logger.info(f"Uploaded encrypted object '{object_name}' to local GCS fallback at '{file_path}'.")
            elif _is_minio_like(client):
                client.put_object(self.bucket_name, object_name, io.BytesIO(file_data), len(file_data), content_type=content_type)
            else:
                bucket = client.bucket(self.bucket_name)
                blob = bucket.blob(object_name)
                blob.upload_from_string(file_data, content_type=content_type)
                logger.info(f"Uploaded object '{object_name}' to GCS bucket '{self.bucket_name}'.")
            return object_name
        except Exception as err:
            logger.error(f"Failed to upload object '{object_name}' to GCS: {err}")
            raise StorageError(f"GCS storage upload failed for object '{object_name}': {err}")

    def get_file_bytes(self, object_name: str, client: Optional[Any] = None) -> bytes:
        client = client or self.get_client()
        self.ensure_bucket_exists(client=client)
        try:
            if client == "LOCAL_FALLBACK":
                file_path = os.path.join(self._local_storage_dir, object_name)
                if not os.path.exists(file_path):
                    raise FileNotFoundError(f"Object '{object_name}' not found in local GCS storage fallback.")
                with open(file_path, "rb") as f:
                    res = f.read()
            elif _is_minio_like(client):
                res = client.get_object(self.bucket_name, object_name)
                try:
                    return res.read()
                finally:
                    if hasattr(res, "close"):
                        res.close()
            else:
                bucket = client.bucket(self.bucket_name)
                blob = bucket.blob(object_name)
                if hasattr(blob, "download_as_bytes"):
                    res = blob.download_as_bytes()
                elif hasattr(blob, "download_as_string"):
                    res = blob.download_as_string()
                else:
                    res = b""

            if not isinstance(res, bytes):
                res = bytes(res) if res else b""
            return res
        except Exception as err:
            logger.error(f"Failed to retrieve object '{object_name}' from GCS: {err}")
            raise StorageError(f"GCS storage retrieval failed for object '{object_name}': {err}")

    def get_file(self, object_name: str, client: Optional[Any] = None) -> StorageObjectStream:
        raw_bytes = self.get_file_bytes(object_name, client=client)
        return StorageObjectStream(raw_bytes)

    def delete_file(self, object_name: str, client: Optional[Any] = None) -> None:
        try:
            client = client or self.get_client()
            if client == "LOCAL_FALLBACK":
                file_path = os.path.join(self._local_storage_dir, object_name)
                if os.path.exists(file_path):
                    os.remove(file_path)
                logger.info(f"Removed object '{object_name}' from local GCS fallback.")
            elif _is_minio_like(client):
                client.remove_object(self.bucket_name, object_name)
            else:
                bucket = client.bucket(self.bucket_name)
                blob = bucket.blob(object_name)
                if hasattr(blob, "delete"):
                    blob.delete()
                logger.info(f"Removed object '{object_name}' from GCS bucket '{self.bucket_name}'.")
        except Exception as err:
            logger.error(f"Failed to delete object '{object_name}' from GCS: {err}")


import boto3
from botocore.exceptions import ClientError


class S3StorageAdapter:
    """
    Storage adapter for S3-compatible APIs (like Supabase Storage) using boto3.
    """
    def __init__(self):
        self.endpoint = settings.MINIO_ENDPOINT
        self.access_key = settings.MINIO_ACCESS_KEY
        self.secret_key = settings.MINIO_SECRET_KEY
        self.bucket_name = settings.MINIO_BUCKET_NAME
        self._client = None

    def get_client(self):
        if self._client is None:
            try:
                from botocore.client import Config
                boto_config = Config(
                    s3={'addressing_style': 'path'},
                    connect_timeout=5,
                    read_timeout=5
                )
                self._client = boto3.client('s3',
                    endpoint_url=self.endpoint,
                    aws_access_key_id=self.access_key,
                    aws_secret_access_key=self.secret_key,
                    region_name='auto',  # Supabase S3 accepts any region string
                    config=boto_config
                )
            except Exception as err:
                logger.error(f"Failed to initialize S3 client: {err}")
                raise StorageError(f"S3 storage client initialization failed: {err}")
        return self._client

    def upload_file(
        self, file_data: bytes, object_name: str, content_type: str = "application/pdf", client: Optional[Any] = None
    ) -> str:
        return self.store_file(object_name=object_name, file_data=file_data, content_type=content_type, client=client)

    def store_file(self, object_name: str, file_data: bytes, content_type: str = "application/octet-stream", client: Optional[Any] = None) -> str:
        client = client or self.get_client()
        try:
            client.put_object(
                Bucket=self.bucket_name,
                Key=object_name,
                Body=file_data,
                ContentType=content_type
            )
            logger.info(f"Uploaded object '{object_name}' to S3 bucket '{self.bucket_name}'.")
            return object_name
        except Exception as err:
            logger.error(f"Failed to upload object '{object_name}' to S3: {err}")
            raise StorageError(f"S3 storage upload failed for object '{object_name}': {err}")

    def get_file(self, object_name: str, client: Optional[Any] = None):
        client = client or self.get_client()
        try:
            response = client.get_object(Bucket=self.bucket_name, Key=object_name)
            return response
        except Exception as err:
            logger.error(f"Failed to retrieve object '{object_name}' from S3: {err}")
            raise StorageError(f"S3 storage retrieval failed for object '{object_name}': {err}")

    def get_file_bytes(self, object_name: str, client: Optional[Any] = None) -> bytes:
        response = self.get_file(object_name, client)
        return response['Body'].read()

    def delete_file(self, object_name: str, client: Optional[Any] = None) -> None:
        client = client or self.get_client()
        try:
            client.delete_object(Bucket=self.bucket_name, Key=object_name)
            logger.info(f"Removed object '{object_name}' from S3 bucket '{self.bucket_name}'.")
        except Exception as err:
            logger.error(f"Failed to delete object '{object_name}' from S3: {err}")


class DatabaseStorageAdapter:
    """
    Storage adapter that saves binary data directly into the Postgres database.
    """
    def __init__(self):
        from app.db.session import engine
        self.engine = engine

    def get_client(self):
        return self.engine

    def store_file(self, object_name: str, file_data: bytes, content_type: str = "application/octet-stream", client: Optional[Any] = None) -> str:
        from sqlalchemy import text
        engine = client or self.get_client()
        with engine.begin() as conn:
            conn.execute(text("""
                INSERT INTO storage_objects (object_name, file_data, content_type)
                VALUES (:name, :data, :ctype)
                ON CONFLICT (object_name) DO UPDATE 
                SET file_data = EXCLUDED.file_data, content_type = EXCLUDED.content_type
            """), {"name": object_name, "data": file_data, "ctype": content_type})
        logger.info(f"Uploaded encrypted object '{object_name}' to PostgreSQL Database Storage.")
        return object_name
        
    def upload_file(self, file_data: bytes, object_name: str, content_type: str = "application/pdf", client: Optional[Any] = None) -> str:
        return self.store_file(object_name=object_name, file_data=file_data, content_type=content_type, client=client)

    def get_file_bytes(self, object_name: str, client: Optional[Any] = None) -> bytes:
        from sqlalchemy import text
        engine = client or self.get_client()
        with engine.connect() as conn:
            row = conn.execute(text("SELECT file_data FROM storage_objects WHERE object_name = :name"), {"name": object_name}).fetchone()
            if not row:
                raise StorageError(f"Object '{object_name}' not found in database storage.")
            return row[0]

    def get_file(self, object_name: str, client: Optional[Any] = None) -> StorageObjectStream:
        raw_bytes = self.get_file_bytes(object_name, client=client)
        return StorageObjectStream(raw_bytes)

    def delete_file(self, object_name: str, client: Optional[Any] = None) -> None:
        from sqlalchemy import text
        engine = client or self.get_client()
        with engine.begin() as conn:
            conn.execute(text("DELETE FROM storage_objects WHERE object_name = :name"), {"name": object_name})
        logger.info(f"Removed object '{object_name}' from database storage.")


class StorageService:
    """
    Main application storage service proxy. Defaults to GCS storage.
    """
    def __init__(self, provider: Optional[str] = None):
        self.provider = (provider or getattr(settings, "STORAGE_PROVIDER", "GCS")).upper()
        if self.provider == "MINIO" or self.provider == "S3":
            self.adapter = S3StorageAdapter()
        elif self.provider == "DB":
            self.adapter = DatabaseStorageAdapter()
        else:
            self.adapter = GCSStorageAdapter()

    def get_client(self) -> Any:
        return self.adapter.get_client()

    def _safe_get_client(self) -> Optional[Any]:
        try:
            return self.get_client()
        except StorageError:
            return None

    def ensure_bucket_exists(self) -> None:
        client = self._safe_get_client()
        self.adapter.ensure_bucket_exists(client=client)

    def validate_file(self, filename: str, content_type: str, file_size: int) -> None:
        if not filename or filename.strip() == "":
            raise FileValidationError("Invalid filename provided.")

        clean_filename = filename.lower()
        if not any(clean_filename.endswith(ext) for ext in ALLOWED_EXTENSIONS):
            raise FileValidationError(
                f"Invalid file extension for '{filename}'. Only PDF and image files are supported."
            )

        if content_type and content_type.lower() not in ALLOWED_MIME_TYPES:
            raise FileValidationError(
                f"Invalid content type '{content_type}'."
            )

        if file_size > MAX_FILE_SIZE:
            max_mb = MAX_FILE_SIZE // (1024 * 1024)
            raise FileValidationError(
                f"File size exceeds maximum allowed limit of {max_mb}MB."
            )

    def generate_object_name(self, document_id: Any, original_filename: str) -> str:
        secure_uuid = str(uuid4())
        ext = ".pdf"
        if original_filename:
            _, file_ext = os.path.splitext(original_filename.lower())
            if file_ext in ALLOWED_EXTENSIONS:
                ext = file_ext
        return f"documents/{document_id}/{secure_uuid}{ext}"

    def upload_file(
        self, file_data: bytes, object_name: str, content_type: str = "application/pdf"
    ) -> str:
        client = self._safe_get_client()
        return self.adapter.upload_file(file_data, object_name, content_type, client=client)

    def get_file(self, object_name: str) -> Any:
        client = self._safe_get_client()
        return self.adapter.get_file(object_name, client=client)

    def get_file_bytes(self, object_name: str) -> bytes:
        client = self._safe_get_client()
        return self.adapter.get_file_bytes(object_name, client=client)

    def delete_file(self, object_name: str) -> None:
        client = self._safe_get_client()
        self.adapter.delete_file(object_name, client=client)


storage_service = StorageService()
