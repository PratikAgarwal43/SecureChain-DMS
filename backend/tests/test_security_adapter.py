"""
SecureChain DMS — Security Adapter Unit Tests
==============================================
Tests for `app.services.security_adapter.SecurityAdapter`.
Covers SHA-256 verification, evidence upload (Two-Vault packaging), retrieval/decryption,
chain verification intact/tampered, invalid hash detection, exception handling,
and custom/fallback KEK configuration.
"""

import hashlib
import sys
from pathlib import Path

# Ensure services/security-and-database is in sys.path before importing securechain_security
security_pkg_dir = Path(__file__).resolve().parents[2] / "services" / "security-and-database"
if security_pkg_dir.exists() and str(security_pkg_dir) not in sys.path:
    sys.path.insert(0, str(security_pkg_dir))

import pytest
from securechain_security.chain_verifier import VerificationError
from securechain_security.encryption_service import DecryptionError
from securechain_security.hash_service import HashingError
from securechain_security.models import ChainStatus, VaultPackage, VerificationResult
from securechain_security.vault_router import VaultRoutingError

from app.services.security_adapter import SecurityAdapter, security_adapter


def test_verify_content_hash_success_and_failure():
    """Test constant-time SHA-256 content verification for valid and invalid hashes."""
    data = b"Digital Evidence Sample Content 123"
    correct_hash = hashlib.sha256(data).hexdigest()
    wrong_hash = "a" * 64

    adapter = SecurityAdapter()
    assert adapter.verify_content_hash(data, correct_hash) is True
    assert adapter.verify_content_hash(data, wrong_hash) is False


def test_process_evidence_upload():
    """Test evidence upload produces segregated VaultPackage with required metadata."""
    adapter = SecurityAdapter()
    payload = b"Top Secret Judicial Evidence File"
    doc_id = "doc-test-101"
    case_id = "case-test-900"
    officer_id = "officer-test-42"

    package = adapter.process_evidence_upload(
        plaintext=payload,
        document_id=doc_id,
        case_id=case_id,
        officer_id=officer_id,
        version="1.0",
    )

    assert isinstance(package, VaultPackage)
    assert package.document_id == doc_id
    assert package.case_id == case_id
    assert isinstance(package.vault2_blob, bytes)
    assert len(package.vault2_blob) > 0

    meta = package.vault1_metadata
    assert "chain_record" in meta
    assert "wrapped_dek" in meta
    assert "aad" in meta
    assert "doc_hash" in meta
    assert "iv" in meta

    assert meta["doc_hash"] == hashlib.sha256(payload).hexdigest()
    assert adapter.vault_router.validate_vault_separation(package) is True


def test_process_evidence_retrieval():
    """Test evidence retrieval and decryption recombines Vault 1 and Vault 2 correctly."""
    adapter = SecurityAdapter()
    payload = b"Confidential Court Evidence Payload - BSA 2023"
    doc_id = "doc-retrieval-1"
    case_id = "case-retrieval-1"
    officer_id = "officer-77"

    package = adapter.process_evidence_upload(
        plaintext=payload,
        document_id=doc_id,
        case_id=case_id,
        officer_id=officer_id,
    )

    retrieved = adapter.process_evidence_retrieval(
        vault1_metadata=package.vault1_metadata,
        vault2_blob=package.vault2_blob,
        expected_doc_hash=package.vault1_metadata["doc_hash"],
    )

    assert retrieved == payload


def test_chain_verification_success():
    """Test chain verification reports INTACT status for valid uploads."""
    adapter = SecurityAdapter()
    case_id = "case-chain-intact"

    adapter.process_evidence_upload(
        plaintext=b"Doc 1 payload",
        document_id="doc-1",
        case_id=case_id,
        officer_id="officer-1",
    )

    res = adapter.verify_document_chain(case_id)
    assert isinstance(res, VerificationResult)
    assert res.status == ChainStatus.INTACT
    assert res.documents_checked == 1
    assert res.documents_valid == 1


def test_chain_verification_tamper_detection():
    """Test chain verification detects tampering when a link is altered."""
    adapter = SecurityAdapter()
    case_id = "case-chain-tampered"

    adapter.process_evidence_upload(
        plaintext=b"Original Payload",
        document_id="doc-tamper-1",
        case_id=case_id,
        officer_id="officer-1",
    )

    # Tamper with internal chain record doc_hash
    chain = adapter.chain_engine._chains[case_id]
    original_record = chain[0]

    tampered_record = type(original_record)(
        document_id=original_record.document_id,
        case_id=original_record.case_id,
        version=original_record.version,
        doc_hash="f" * 64,  # Corrupted doc hash
        chain_hash=original_record.chain_hash,
        prev_chain_hash=original_record.prev_chain_hash,
        timestamp=original_record.timestamp,
        officer_id=original_record.officer_id,
        sequence_number=original_record.sequence_number,
        quorum_token=original_record.quorum_token,
        amendment_of=original_record.amendment_of,
    )
    chain[0] = tampered_record

    res = adapter.verify_document_chain(case_id)
    assert isinstance(res, VerificationResult)
    assert res.status == ChainStatus.TAMPERED


def test_invalid_hash_detection_retrieval_mismatch():
    """Test retrieval fails when expected_doc_hash does not match plaintext hash."""
    adapter = SecurityAdapter()
    payload = b"Authentic payload"

    package = adapter.process_evidence_upload(
        plaintext=payload,
        document_id="doc-mismatch",
        case_id="case-mismatch",
        officer_id="officer-1",
    )

    wrong_expected_hash = "b" * 64

    with pytest.raises((VaultRoutingError, DecryptionError)):
        adapter.process_evidence_retrieval(
            vault1_metadata=package.vault1_metadata,
            vault2_blob=package.vault2_blob,
            expected_doc_hash=wrong_expected_hash,
        )


def test_exception_handling_invalid_inputs():
    """Test invalid input types raise appropriate security layer exceptions."""
    adapter = SecurityAdapter()

    with pytest.raises(VaultRoutingError):
        adapter.process_evidence_upload(
            plaintext=None,
            document_id="doc-err",
            case_id="case-err",
            officer_id="off-err",
        )

    with pytest.raises(VaultRoutingError):
        adapter.process_evidence_retrieval(
            vault1_metadata={},
            vault2_blob=b"corrupted",
        )

    with pytest.raises(HashingError):
        adapter.verify_content_hash(
            plaintext=b"some data",
            expected_doc_hash="",
        )


def test_configuration_fallback_and_custom_master_kek():
    """Test SecurityAdapter initialization with fallback vs explicit MASTER_KEK."""
    # Test default fallback instance
    adapter_default = SecurityAdapter()
    assert adapter_default.encryption_service.key_manager.current_kek_version == "v1"

    # Test custom hex master_kek instance
    custom_hex_kek = "01" * 32
    adapter_custom = SecurityAdapter(master_kek=custom_hex_kek, kek_version="v2")
    assert adapter_custom.encryption_service.key_manager.current_kek_version == "v2"

    payload = b"Data encrypted under custom KEK"
    pkg = adapter_custom.process_evidence_upload(
        plaintext=payload,
        document_id="doc-custom-kek",
        case_id="case-custom-kek",
        officer_id="officer-kek",
    )

    retrieved = adapter_custom.process_evidence_retrieval(
        vault1_metadata=pkg.vault1_metadata,
        vault2_blob=pkg.vault2_blob,
        expected_doc_hash=pkg.vault1_metadata["doc_hash"],
    )

    assert retrieved == payload


def test_singleton_export():
    """Test module-level singleton instance export."""
    assert security_adapter is not None
    assert isinstance(security_adapter, SecurityAdapter)
