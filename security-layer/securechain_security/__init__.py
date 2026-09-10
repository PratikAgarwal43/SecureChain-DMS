"""
SecureChain DMS — Security Layer
================================
Cryptographic security modules for the Zero-Trust Digital Evidence Vault.

Provides:
    - SHA-256 hash generation and hash-chain linking
    - AES-256-GCM envelope encryption with Two-Vault separation
    - Chain integrity verification and tamper detection
    - Merkle tree global anchoring
    - Secure memory handling for key material

SIH26190 — Indian Justice System Digital Evidence Vault
"""

__version__ = "0.1.0"
__project__ = "SecureChain DMS"

from securechain_security.chain_engine import (
    ChainEngine,
    ChainError,
    ChainImmutabilityError,
    ChainNotFoundError,
    QuorumRequiredError,
)
from securechain_security.chain_verifier import (
    ChainVerifier,
    DocumentVerificationResult,
    VerificationError,
)
from securechain_security.encryption_service import (
    CryptoError,
    DecryptionError,
    EncryptionError,
    EncryptionService,
)
from securechain_security.hash_service import HashService, HashingError
from securechain_security.key_manager import (
    KeyManagementError,
    KeyManager,
    KMSProvider,
    LocalKMSProvider,
    zero_buffer,
)
from securechain_security.merkle_checkpoint import (
    MerkleCheckpointEngine,
    MerkleCheckpointError,
)
from securechain_security.tamper_alerts import (
    TamperAlertError,
    TamperAlertSystem,
)
from securechain_security.vault_router import VaultRouter, VaultRoutingError

__all__ = [
    "ChainEngine",
    "ChainError",
    "ChainImmutabilityError",
    "ChainNotFoundError",
    "ChainVerifier",
    "CryptoError",
    "DecryptionError",
    "DocumentVerificationResult",
    "EncryptionError",
    "EncryptionService",
    "HashService",
    "HashingError",
    "KeyManager",
    "KeyManagementError",
    "KMSProvider",
    "LocalKMSProvider",
    "MerkleCheckpointEngine",
    "MerkleCheckpointError",
    "QuorumRequiredError",
    "TamperAlertError",
    "TamperAlertSystem",
    "VaultRouter",
    "VaultRoutingError",
    "VerificationError",
    "zero_buffer",
]



