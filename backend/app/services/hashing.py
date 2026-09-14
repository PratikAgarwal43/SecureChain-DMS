import hashlib
import logging

logger = logging.getLogger(__name__)


def calculate_sha256(file_bytes: bytes) -> str:
    """
    Calculates the 64-character hexadecimal SHA-256 hash digest directly
    from raw file bytes.
    """
    if not isinstance(file_bytes, (bytes, bytearray)):
        raise TypeError("Expected raw file bytes for SHA-256 hash calculation.")
    
    sha256_hash = hashlib.sha256(file_bytes).hexdigest()
    return sha256_hash


def verify_sha256(file_bytes: bytes, expected_hash: str) -> bool:
    """
    Calculates the SHA-256 digest of file_bytes and compares it against expected_hash.
    Returns True if hashes match, False otherwise.
    """
    if not expected_hash:
        return False
    
    computed_hash = calculate_sha256(file_bytes)
    return computed_hash.lower() == expected_hash.lower().strip()
