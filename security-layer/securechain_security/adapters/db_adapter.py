import os
import psycopg2
from psycopg2.extras import DictCursor
import logging
from typing import Optional

from securechain_security.models import VaultPackage

logger = logging.getLogger(__name__)

class DatabaseAdapter:
    """
    Adapter for storing Vault 1 metadata into PostgreSQL.
    Requires DB_DSN environment variable or individual DB variables.
    """

    def __init__(self, dsn: Optional[str] = None):
        self.dsn = dsn or os.environ.get(
            "DATABASE_URL", 
            "postgresql://postgres:postgres@localhost:5432/securechain_db"
        )
        self.conn = None

    def connect(self):
        if not self.conn or self.conn.closed:
            self.conn = psycopg2.connect(self.dsn)
            self.conn.autocommit = False

    def close(self):
        if self.conn and not self.conn.closed:
            self.conn.close()

    def store_vault_package(
        self, 
        package: VaultPackage, 
        title: str, 
        document_type: str, 
        sensitivity_level: str,
        file_size: int,
        mime_type: str,
        original_filename: str
    ):
        """
        Stores the Vault 1 metadata into the documents and document_versions tables.
        Handles the circular foreign key DEFERRABLE pattern automatically.
        """
        self.connect()
        v1 = package.vault1_metadata
        chain = v1["chain_record"]

        officer_id = chain["officer_id"]
        case_id = chain["case_id"]
        doc_id = chain["document_id"]
        version = chain["version"]

        try:
            with self.conn.cursor() as cur:
                # STEP 1: If v1.0, insert the main document record with current_version_id = NULL
                if version == 1:
                    cur.execute('''
                        INSERT INTO documents 
                        (id, case_id, title, document_type, sensitivity_level, status, created_by)
                        VALUES (%s, %s, %s, %s, %s, 'LOCKED', %s)
                    ''', (doc_id, case_id, title, document_type, sensitivity_level, officer_id))
                
                # STEP 2: Insert the immutable document_version
                cur.execute('''
                    INSERT INTO document_versions (
                        document_id, version_number, storage_key, 
                        doc_hash, chain_hash, prev_chain_hash, quorum_token,
                        wrapped_dek, iv, key_id, kek_version, aad, algorithm,
                        file_size, mime_type, original_filename,
                        created_by, status
                    ) VALUES (
                        %s, %s, %s,
                        %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s,
                        %s, %s, %s,
                        %s, 'LOCKED'
                    ) RETURNING id
                ''', (
                    doc_id, version, package.vault2_blob_ref,
                    v1["doc_hash"], chain["chain_hash"], chain["prev_chain_hash"], chain.get("quorum_token"),
                    v1["wrapped_dek"], v1["iv"], v1.get("key_id"), v1.get("kek_version"), v1["aad"], v1.get("algorithm", "AES-256-GCM"),
                    file_size, mime_type, original_filename,
                    officer_id
                ))
                version_id = cur.fetchone()[0]

                # STEP 3: Update the document's current_version_id (closes the circular FK loop)
                cur.execute('''
                    UPDATE documents 
                    SET current_version_id = %s, updated_at = NOW()
                    WHERE id = %s
                ''', (version_id, doc_id))

                # Commit transaction
                self.conn.commit()
                logger.info(f"Successfully committed Vault 1 metadata to Postgres. Doc: {doc_id} v{version}")
                
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Failed to store Vault 1 metadata: {e}")
            raise
        
    def get_vault_metadata(self, document_id: str, version_number: int) -> dict:
        """
        Retrieves Vault 1 metadata to pass back into process_retrieval()
        """
        self.connect()
        try:
            with self.conn.cursor(cursor_factory=DictCursor) as cur:
                cur.execute('''
                    SELECT 
                        doc_hash, chain_hash, prev_chain_hash, quorum_token,
                        wrapped_dek, iv, key_id, kek_version, aad, algorithm,
                        storage_key
                    FROM document_versions
                    WHERE document_id = %s AND version_number = %s
                ''', (document_id, version_number))
                row = cur.fetchone()
                
                if not row:
                    raise ValueError("Document version not found")

                # Reconstruct Vault1 dictionary
                v1_metadata = {
                    "wrapped_dek": row["wrapped_dek"],
                    "aad": row["aad"],
                    "doc_hash": row["doc_hash"],
                    "iv": row["iv"],
                    "algorithm": row["algorithm"],
                    "kek_version": row["kek_version"],
                    "key_id": str(row["key_id"]),
                    "chain_record": {
                        "document_id": document_id,
                        "version": version_number,
                        "doc_hash": row["doc_hash"],
                        "chain_hash": row["chain_hash"],
                        "prev_chain_hash": row["prev_chain_hash"],
                        "quorum_token": row["quorum_token"],
                    }
                }
                return v1_metadata, row["storage_key"]
                
        except Exception as e:
            logger.error(f"Failed to get Vault 1 metadata: {e}")
            raise
