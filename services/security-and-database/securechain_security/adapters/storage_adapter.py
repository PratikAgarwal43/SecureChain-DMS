import os
import boto3
import logging
from botocore.exceptions import ClientError
from typing import Optional

logger = logging.getLogger(__name__)

class CloudflareR2Adapter:
    """
    Adapter for storing Vault 2 encrypted blobs into Cloudflare R2 (S3 compatible).
    Requires the following environment variables:
      - R2_ACCOUNT_ID
      - R2_ACCESS_KEY_ID
      - R2_SECRET_ACCESS_KEY
      - R2_BUCKET_NAME
    """

    def __init__(self):
        self.account_id = os.environ.get("R2_ACCOUNT_ID")
        self.access_key = os.environ.get("R2_ACCESS_KEY_ID")
        self.secret_key = os.environ.get("R2_SECRET_ACCESS_KEY")
        self.bucket_name = os.environ.get("R2_BUCKET_NAME", "securechain-vault2")

        if not all([self.account_id, self.access_key, self.secret_key]):
            logger.warning("Cloudflare R2 credentials missing. Storage will fail if called.")

        endpoint_url = f"https://{self.account_id}.r2.cloudflarestorage.com"

        self.s3_client = boto3.client(
            service_name="s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            region_name="auto",  # R2 requires 'auto' or 'wnam' etc.
        )

    def store_blob(self, storage_key: str, data: bytes) -> bool:
        """
        Stores the Vault 2 encrypted blob in Cloudflare R2.
        
        Args:
            storage_key: The path in the bucket (e.g., '{case_id}/{document_id}/{version}.enc')
            data: The ciphertext bytes.
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=storage_key,
                Body=data,
                ContentType="application/octet-stream"
            )
            logger.info(f"Successfully stored blob to R2: {storage_key}")
            return True
        except ClientError as e:
            logger.error(f"Failed to store blob to R2: {e}")
            raise

    def retrieve_blob(self, storage_key: str) -> bytes:
        """
        Retrieves the Vault 2 encrypted blob from Cloudflare R2.
        
        Args:
            storage_key: The path in the bucket.
            
        Returns:
            The ciphertext bytes.
        """
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=storage_key
            )
            data = response['Body'].read()
            logger.info(f"Successfully retrieved blob from R2: {storage_key}")
            return data
        except ClientError as e:
            logger.error(f"Failed to retrieve blob from R2: {e}")
            raise
