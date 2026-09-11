"""
Unit tests for SecureChain DMS Hash Generator Service (Module 1).
Uses unittest from standard library for compatibility with all environments.
"""

import hashlib
import io
import logging
import unittest
from concurrent.futures import ThreadPoolExecutor

from securechain_security.hash_service import HashService, HashingError
from securechain_security.models import GENESIS_HASH, HASH_ALGORITHM, HashResult


class BrokenStream:
    """Simulates a stream that raises an I/O error on read."""
    def read(self, size=-1):
        raise IOError("Disk read error during evidence reading")


class TestHashService(unittest.TestCase):
    def setUp(self):
        self.service = HashService()

    def test_init_invalid_chunk_size(self):
        with self.assertRaises(ValueError):
            HashService(chunk_size=0)
        with self.assertRaises(ValueError):
            HashService(chunk_size=-1024)

    def test_hash_document_empty_stream(self):
        empty_stream = io.BytesIO(b"")
        digest = self.service.hash_document(empty_stream)
        expected = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        self.assertEqual(digest, expected)

    def test_hash_document_chunked(self):
        # 25,000 bytes spanning > 3 chunks of 8192 bytes
        data = b"A" * 25000
        stream = io.BytesIO(data)
        digest = self.service.hash_document(stream)
        expected = hashlib.sha256(data).hexdigest()
        self.assertEqual(digest, expected)

    def test_hash_document_custom_chunk_size(self):
        data = b"SecureChain Test Payload" * 100
        stream = io.BytesIO(data)
        digest = self.service.hash_document(stream, chunk_size=16)
        expected = hashlib.sha256(data).hexdigest()
        self.assertEqual(digest, expected)

    def test_hash_document_invalid_stream(self):
        with self.assertRaises(HashingError):
            self.service.hash_document("not-a-stream")

        with self.assertRaises(HashingError):
            self.service.hash_document(None)

    def test_hash_document_io_failure(self):
        with self.assertRaises(HashingError) as ctx:
            self.service.hash_document(BrokenStream())
        self.assertIn("Disk read error", str(ctx.exception))
        self.assertIsNotNone(ctx.exception.cause)

    def test_hash_bytes(self):
        data = b"Zero-Trust Digital Evidence Vault"
        digest = self.service.hash_bytes(data)
        self.assertEqual(digest, hashlib.sha256(data).hexdigest())

    def test_hash_bytes_empty(self):
        digest = self.service.hash_bytes(b"")
        self.assertEqual(digest, "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855")

    def test_hash_bytes_invalid_input(self):
        with self.assertRaises(HashingError):
            self.service.hash_bytes("not-bytes")  # type: ignore

    def test_hash_chain_link_without_quorum(self):
        doc_hash = "a" * 64
        prev_hash = GENESIS_HASH
        timestamp = "2026-09-04T11:00:00.000Z"
        officer_id = "OFFICER-DL-9842"

        chain_hash = self.service.hash_chain_link(
            doc_hash=doc_hash,
            prev_chain_hash=prev_hash,
            timestamp=timestamp,
            officer_id=officer_id,
        )

        expected_payload = f"{doc_hash}{prev_hash}{timestamp}{officer_id}".encode("utf-8")
        expected_hash = hashlib.sha256(expected_payload).hexdigest()
        self.assertEqual(chain_hash, expected_hash)

    def test_hash_chain_link_with_quorum(self):
        doc_hash = "b" * 64
        prev_hash = "c" * 64
        timestamp = "2026-09-04T11:05:00.000Z"
        officer_id = "OFFICER-MH-4512"
        quorum_token = "QUORUM-SIG-MULTI-PARTY-998877"

        chain_hash = self.service.hash_chain_link(
            doc_hash=doc_hash,
            prev_chain_hash=prev_hash,
            timestamp=timestamp,
            officer_id=officer_id,
            quorum_token=quorum_token,
        )

        expected_payload = f"{doc_hash}{prev_hash}{timestamp}{officer_id}{quorum_token}".encode("utf-8")
        expected_hash = hashlib.sha256(expected_payload).hexdigest()
        self.assertEqual(chain_hash, expected_hash)

    def test_hash_chain_link_validation_errors(self):
        with self.assertRaises(HashingError):
            self.service.hash_chain_link("", "prev", "time", "officer")
        with self.assertRaises(HashingError):
            self.service.hash_chain_link("doc", "", "time", "officer")
        with self.assertRaises(HashingError):
            self.service.hash_chain_link("doc", "prev", "", "officer")
        with self.assertRaises(HashingError):
            self.service.hash_chain_link("doc", "prev", "time", "")
        with self.assertRaises(HashingError):
            self.service.hash_chain_link("doc", "prev", "time", "officer", quorum_token=123)  # type: ignore

    def test_verify_hash_success(self):
        data = b"Evidence seizure record #9012"
        stream = io.BytesIO(data)
        expected = hashlib.sha256(data).hexdigest()
        self.assertTrue(self.service.verify_hash(stream, expected))

    def test_verify_hash_case_insensitive(self):
        data = b"Case-insensitive test data"
        stream = io.BytesIO(data)
        expected = hashlib.sha256(data).hexdigest().upper()
        self.assertTrue(self.service.verify_hash(stream, expected))

    def test_verify_hash_mismatch(self):
        data = b"Authentic evidence content"
        stream = io.BytesIO(data)
        tampered_hash = "f" * 64
        self.assertFalse(self.service.verify_hash(stream, tampered_hash))

    def test_verify_hash_invalid_expected(self):
        stream = io.BytesIO(b"data")
        with self.assertRaises(HashingError):
            self.service.verify_hash(stream, "")

    def test_hash_multiple_streams(self):
        streams = [
            io.BytesIO(b"file 1 content"),
            io.BytesIO(b"file 2 content"),
            io.BytesIO(b"file 3 content"),
        ]
        results = self.service.hash_multiple(streams)
        self.assertEqual(len(results), 3)
        for res, original_stream in zip(results, streams):
            self.assertIsInstance(res, HashResult)
            self.assertEqual(res.algorithm, HASH_ALGORITHM)
            self.assertEqual(res.file_size_bytes, len(original_stream.getvalue()))
            self.assertEqual(res.doc_hash, hashlib.sha256(original_stream.getvalue()).hexdigest())

    def test_hash_multiple_tuples(self):
        items = [
            ("DOC-001", io.BytesIO(b"Payload 1")),
            ("DOC-002", io.BytesIO(b"Payload 2")),
        ]
        results = self.service.hash_multiple(items)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].document_id, "DOC-001")
        self.assertEqual(results[1].document_id, "DOC-002")
        self.assertEqual(results[0].file_size_bytes, len(b"Payload 1"))

    def test_hash_multiple_dicts(self):
        items = [
            {"document_id": "EVID-A", "stream": io.BytesIO(b"Audio record")},
            {"document_id": "EVID-V", "stream": io.BytesIO(b"Video record")},
        ]
        results = self.service.hash_multiple(items)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].document_id, "EVID-A")
        self.assertEqual(results[1].document_id, "EVID-V")

    def test_hash_multiple_empty_and_none(self):
        self.assertEqual(self.service.hash_multiple([]), [])
        with self.assertRaises(HashingError):
            self.service.hash_multiple(None)  # type: ignore

    def test_hash_multiple_failure_handling(self):
        items = [
            ("DOC-OK", io.BytesIO(b"OK")),
            ("DOC-FAIL", BrokenStream()),
        ]
        with self.assertRaises(HashingError) as ctx:
            self.service.hash_multiple(items)
        self.assertIn("DOC-FAIL", str(ctx.exception))

    def test_thread_safety(self):
        service = HashService()
        def hash_worker(index: int) -> str:
            payload = f"worker payload {index}".encode("utf-8") * 500
            return service.hash_document(io.BytesIO(payload))

        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = [executor.submit(hash_worker, i) for i in range(20)]
            results = [f.result() for f in futures]

        for i, digest in enumerate(results):
            expected = hashlib.sha256((f"worker payload {i}".encode("utf-8") * 500)).hexdigest()
            self.assertEqual(digest, expected)

    def test_logging_no_hash_at_info_level(self):
        logger = logging.getLogger("securechain_security.hash_service")
        records = []

        class ListHandler(logging.Handler):
            def emit(self, record):
                records.append(record)

        handler = ListHandler()
        handler.setLevel(logging.INFO)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

        try:
            data = b"Confidential crime scene log"
            stream = io.BytesIO(data)
            digest = self.service.hash_document(stream)
            info_records = [r for r in records if r.levelno == logging.INFO]
            self.assertTrue(len(info_records) > 0)
            for r in info_records:
                self.assertNotIn(digest, r.getMessage())
        finally:
            logger.removeHandler(handler)


if __name__ == "__main__":
    unittest.main()
