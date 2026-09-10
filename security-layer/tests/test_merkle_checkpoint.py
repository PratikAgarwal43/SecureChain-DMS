"""
Unit tests for SecureChain DMS Merkle Tree Checkpoint Engine (Module 8).
========================================================================
Validates binary Merkle tree construction, deterministic root hashing, odd-leaf
duplication, checkpoint generation, post-checkpoint chain mutation detection,
logarithmic Merkle inclusion proofs, invalid proof rejection, and multi-case anchoring.
"""

from __future__ import annotations

import unittest

from securechain_security.chain_engine import ChainEngine
from securechain_security.hash_service import HashService
from securechain_security.merkle_checkpoint import (
    MerkleCheckpointEngine,
    MerkleCheckpointError,
)
from securechain_security.models import (
    GENESIS_HASH,
    MerkleCheckpoint,
)


class TestMerkleCheckpointEngine(unittest.TestCase):
    """Test suite for MerkleCheckpointEngine."""

    def setUp(self) -> None:
        """Set up fresh HashService, ChainEngine, and MerkleCheckpointEngine."""
        self.hash_service = HashService()
        self.chain_engine = ChainEngine(hash_service=self.hash_service)
        self.engine = MerkleCheckpointEngine(
            chain_engine=self.chain_engine,
            hash_service=self.hash_service,
        )

        self.officer_id = "OFFICER-REGISTRY-DSC-001"

    # -----------------------------------------------------------------------
    # Initialization & Properties
    # -----------------------------------------------------------------------

    def test_init_and_properties(self) -> None:
        """Engine initializes with injected dependencies and empty checkpoint store."""
        self.assertIs(self.engine.chain_engine, self.chain_engine)
        self.assertIs(self.engine.hash_service, self.hash_service)
        self.assertEqual(len(self.engine.get_checkpoints()), 0)

        # Getting latest checkpoint when none exist raises error
        with self.assertRaises(MerkleCheckpointError):
            self.engine.get_latest_checkpoint()

    def test_init_validation_rejects_none(self) -> None:
        """Initialization fails if either dependency is None."""
        with self.assertRaises(MerkleCheckpointError):
            MerkleCheckpointEngine(chain_engine=None, hash_service=self.hash_service)  # type: ignore
        with self.assertRaises(MerkleCheckpointError):
            MerkleCheckpointEngine(chain_engine=self.chain_engine, hash_service=None)  # type: ignore

    # -----------------------------------------------------------------------
    # Merkle Tree Construction & Edge Cases
    # -----------------------------------------------------------------------

    def test_merkle_tree_empty_leaves_returns_genesis_hash(self) -> None:
        """Empty leaf list returns GENESIS_HASH (64 zeros)."""
        root = self.engine.build_merkle_tree([])
        self.assertEqual(root, GENESIS_HASH)

    def test_merkle_tree_single_leaf(self) -> None:
        """Single leaf returns that leaf's hash directly."""
        leaf = self.hash_service.hash_bytes(b"single-leaf-payload")
        root = self.engine.build_merkle_tree([leaf])
        self.assertEqual(root, leaf)

    def test_merkle_tree_two_leaves_known_inputs(self) -> None:
        """Two leaves combine as SHA-256(left + right)."""
        h1 = self.hash_service.hash_bytes(b"leaf-1")
        h2 = self.hash_service.hash_bytes(b"leaf-2")

        expected_root = self.hash_service.hash_bytes((h1 + h2).encode("utf-8"))
        actual_root = self.engine.build_merkle_tree([h1, h2])

        self.assertEqual(actual_root, expected_root)

    def test_merkle_tree_odd_number_of_leaves(self) -> None:
        """Odd number of leaves (3 leaves) duplicates the trailing leaf to balance pairs."""
        h1 = self.hash_service.hash_bytes(b"leaf-1")
        h2 = self.hash_service.hash_bytes(b"leaf-2")
        h3 = self.hash_service.hash_bytes(b"leaf-3")

        # Manual level calculation:
        # Level 0: [h1, h2, h3, h3]
        # Level 1: [H(h1 + h2), H(h3 + h3)]
        p0 = self.hash_service.hash_bytes((h1 + h2).encode("utf-8"))
        p1 = self.hash_service.hash_bytes((h3 + h3).encode("utf-8"))
        expected_root = self.hash_service.hash_bytes((p0 + p1).encode("utf-8"))

        actual_root = self.engine.build_merkle_tree([h1, h2, h3])
        self.assertEqual(actual_root, expected_root)

    def test_merkle_tree_five_leaves_unbalanced_levels(self) -> None:
        """Tree with 5 leaves balances across multiple intermediate odd levels deterministically."""
        leaves = [self.hash_service.hash_bytes(f"leaf-{i}".encode("utf-8")) for i in range(5)]
        root1 = self.engine.build_merkle_tree(leaves)
        root2 = self.engine.build_merkle_tree(leaves)

        self.assertEqual(len(root1), 64)
        self.assertEqual(root1, root2)

    # -----------------------------------------------------------------------
    # Checkpoint Creation for Multiple Cases
    # -----------------------------------------------------------------------

    def test_create_checkpoint_multiple_cases(self) -> None:
        """create_checkpoint binds multiple active case chain heads into an anchored MerkleCheckpoint."""
        # Initialize 4 cases in ChainEngine
        case_ids = ["CR-MUMBAI-01", "CR-KOLKATA-02", "CR-CHENNAI-03", "CR-DELHI-04"]
        for cid in case_ids:
            doc_hash = self.hash_service.hash_bytes(f"genesis-for-{cid}".encode("utf-8"))
            self.chain_engine.create_genesis(
                case_id=cid,
                document_id=f"DOC-FIR-{cid}",
                doc_hash=doc_hash,
                officer_id=self.officer_id,
            )

        checkpoint = self.engine.create_checkpoint()

        self.assertIsInstance(checkpoint, MerkleCheckpoint)
        self.assertEqual(checkpoint.cases_included, 4)
        self.assertEqual(len(checkpoint.case_chain_heads), 4)
        self.assertEqual(len(checkpoint.merkle_root), 64)

        # Checkpoints list and latest checkpoint updated
        self.assertEqual(len(self.engine.get_checkpoints()), 1)
        self.assertEqual(self.engine.get_latest_checkpoint(), checkpoint)

    def test_create_checkpoint_subset_of_cases(self) -> None:
        """create_checkpoint accepts explicit subset of case IDs."""
        case_ids = ["CASE-A", "CASE-B", "CASE-C"]
        for cid in case_ids:
            self.chain_engine.create_genesis(
                case_id=cid,
                document_id=f"DOC-{cid}",
                doc_hash=self.hash_service.hash_bytes(cid.encode("utf-8")),
                officer_id=self.officer_id,
            )

        # Checkpoint only CASE-A and CASE-C
        cp = self.engine.create_checkpoint(case_ids=["CASE-A", "CASE-C"])
        self.assertEqual(cp.cases_included, 2)
        self.assertIn("CASE-A", cp.case_chain_heads)
        self.assertIn("CASE-C", cp.case_chain_heads)
        self.assertNotIn("CASE-B", cp.case_chain_heads)

    def test_create_checkpoint_empty_cases(self) -> None:
        """create_checkpoint with no initialized cases returns valid checkpoint with GENESIS_HASH."""
        cp = self.engine.create_checkpoint(case_ids=[])
        self.assertEqual(cp.cases_included, 0)
        self.assertEqual(cp.merkle_root, GENESIS_HASH)

    # -----------------------------------------------------------------------
    # Deterministic Ordering (Sorted Case IDs)
    # -----------------------------------------------------------------------

    def test_deterministic_ordering_regardless_of_input_order(self) -> None:
        """Cases supplied in different orders produce identical Merkle roots due to sorting."""
        case_ids = ["CASE-ZETA", "CASE-ALPHA", "CASE-MU"]
        for cid in case_ids:
            self.chain_engine.create_genesis(
                case_id=cid,
                document_id=f"DOC-{cid}",
                doc_hash=self.hash_service.hash_bytes(cid.encode("utf-8")),
                officer_id=self.officer_id,
            )

        cp1 = self.engine.create_checkpoint(case_ids=["CASE-ZETA", "CASE-ALPHA", "CASE-MU"])
        cp2 = self.engine.create_checkpoint(case_ids=["CASE-ALPHA", "CASE-MU", "CASE-ZETA"])

        self.assertEqual(cp1.merkle_root, cp2.merkle_root)

    # -----------------------------------------------------------------------
    # Checkpoint Verification (Intact vs Modified)
    # -----------------------------------------------------------------------

    def test_verify_checkpoint_unmodified_chains_is_valid(self) -> None:
        """verify_checkpoint returns True when all underlying case chains remain unchanged."""
        case_ids = ["CASE-01", "CASE-02", "CASE-03"]
        for cid in case_ids:
            self.chain_engine.create_genesis(
                case_id=cid,
                document_id=f"DOC-{cid}",
                doc_hash=self.hash_service.hash_bytes(cid.encode("utf-8")),
                officer_id=self.officer_id,
            )

        checkpoint = self.engine.create_checkpoint()
        self.assertTrue(self.engine.verify_checkpoint(checkpoint))

    def test_verify_checkpoint_detects_chain_modification(self) -> None:
        """verify_checkpoint returns False immediately if any case chain appends a new document."""
        case_ids = ["CASE-01", "CASE-02"]
        for cid in case_ids:
            self.chain_engine.create_genesis(
                case_id=cid,
                document_id=f"DOC-{cid}",
                doc_hash=self.hash_service.hash_bytes(cid.encode("utf-8")),
                officer_id=self.officer_id,
            )

        checkpoint = self.engine.create_checkpoint()
        self.assertTrue(self.engine.verify_checkpoint(checkpoint))

        # Append document to CASE-01, changing its head_chain_hash
        self.chain_engine.append_document(
            case_id="CASE-01",
            document_id="DOC-CASE-01-EVIDENCE-2",
            doc_hash=self.hash_service.hash_bytes(b"new-evidence"),
            officer_id=self.officer_id,
        )

        # Re-verification must fail because CASE-01 head has advanced
        self.assertFalse(self.engine.verify_checkpoint(checkpoint))

    # -----------------------------------------------------------------------
    # Merkle Proof Generation & Verification
    # -----------------------------------------------------------------------

    def test_merkle_proof_generation_and_verification_four_cases(self) -> None:
        """Every case in a 4-case checkpoint generates a valid Merkle inclusion proof."""
        case_ids = ["CR-01", "CR-02", "CR-03", "CR-04"]
        for cid in case_ids:
            self.chain_engine.create_genesis(
                case_id=cid,
                document_id=f"DOC-{cid}",
                doc_hash=self.hash_service.hash_bytes(cid.encode("utf-8")),
                officer_id=self.officer_id,
            )

        checkpoint = self.engine.create_checkpoint()

        for cid in case_ids:
            leaf_hash = checkpoint.case_chain_heads[cid]
            proof = self.engine.get_merkle_proof(checkpoint, cid)

            # In a 4-leaf binary tree, proof length must be 2 (log2(4))
            self.assertEqual(len(proof), 2)
            for step in proof:
                self.assertIn("hash", step)
                self.assertIn(step["position"], ("left", "right"))

            # Verify proof against the expected checkpoint root
            is_valid = self.engine.verify_merkle_proof(
                leaf_hash=leaf_hash,
                proof=proof,
                expected_root=checkpoint.merkle_root,
            )
            self.assertTrue(is_valid, f"Merkle proof verification failed for {cid}")

    def test_merkle_proof_odd_number_of_cases(self) -> None:
        """Merkle proof generates and verifies correctly for odd case count (3 cases)."""
        case_ids = ["CR-A", "CR-B", "CR-C"]
        for cid in case_ids:
            self.chain_engine.create_genesis(
                case_id=cid,
                document_id=f"DOC-{cid}",
                doc_hash=self.hash_service.hash_bytes(cid.encode("utf-8")),
                officer_id=self.officer_id,
            )

        checkpoint = self.engine.create_checkpoint()

        for cid in case_ids:
            leaf_hash = checkpoint.case_chain_heads[cid]
            proof = self.engine.get_merkle_proof(checkpoint, cid)
            is_valid = self.engine.verify_merkle_proof(
                leaf_hash=leaf_hash,
                proof=proof,
                expected_root=checkpoint.merkle_root,
            )
            self.assertTrue(is_valid)

    def test_merkle_proof_single_case(self) -> None:
        """Single case produces an empty proof that verifies directly against the root."""
        self.chain_engine.create_genesis(
            case_id="SOLO-CASE",
            document_id="DOC-SOLO",
            doc_hash=self.hash_service.hash_bytes(b"solo"),
            officer_id=self.officer_id,
        )

        checkpoint = self.engine.create_checkpoint()
        proof = self.engine.get_merkle_proof(checkpoint, "SOLO-CASE")
        self.assertEqual(proof, [])

        is_valid = self.engine.verify_merkle_proof(
            leaf_hash=checkpoint.case_chain_heads["SOLO-CASE"],
            proof=proof,
            expected_root=checkpoint.merkle_root,
        )
        self.assertTrue(is_valid)

    # -----------------------------------------------------------------------
    # Invalid Merkle Proof Detection
    # -----------------------------------------------------------------------

    def test_invalid_proof_tampered_leaf_hash(self) -> None:
        """Supplying a tampered leaf hash causes verify_merkle_proof to fail."""
        self.chain_engine.create_genesis(
            case_id="CASE-1",
            document_id="DOC-1",
            doc_hash=self.hash_service.hash_bytes(b"d1"),
            officer_id=self.officer_id,
        )
        self.chain_engine.create_genesis(
            case_id="CASE-2",
            document_id="DOC-2",
            doc_hash=self.hash_service.hash_bytes(b"d2"),
            officer_id=self.officer_id,
        )

        checkpoint = self.engine.create_checkpoint()
        proof = self.engine.get_merkle_proof(checkpoint, "CASE-1")

        fake_leaf = "0" * 64
        self.assertFalse(
            self.engine.verify_merkle_proof(
                leaf_hash=fake_leaf,
                proof=proof,
                expected_root=checkpoint.merkle_root,
            )
        )

    def test_invalid_proof_tampered_sibling_hash(self) -> None:
        """Supplying a tampered sibling hash inside the proof causes verification to fail."""
        self.chain_engine.create_genesis(
            case_id="CASE-1",
            document_id="DOC-1",
            doc_hash=self.hash_service.hash_bytes(b"d1"),
            officer_id=self.officer_id,
        )
        self.chain_engine.create_genesis(
            case_id="CASE-2",
            document_id="DOC-2",
            doc_hash=self.hash_service.hash_bytes(b"d2"),
            officer_id=self.officer_id,
        )

        checkpoint = self.engine.create_checkpoint()
        proof = self.engine.get_merkle_proof(checkpoint, "CASE-1")

        # Corrupt the sibling hash
        corrupted_proof = [{"hash": "a" * 64, "position": proof[0]["position"]}]
        self.assertFalse(
            self.engine.verify_merkle_proof(
                leaf_hash=checkpoint.case_chain_heads["CASE-1"],
                proof=corrupted_proof,
                expected_root=checkpoint.merkle_root,
            )
        )

    def test_invalid_proof_inverted_position(self) -> None:
        """Inverting a sibling's position (left vs right) causes verification to fail."""
        self.chain_engine.create_genesis(
            case_id="CASE-1",
            document_id="DOC-1",
            doc_hash=self.hash_service.hash_bytes(b"d1"),
            officer_id=self.officer_id,
        )
        self.chain_engine.create_genesis(
            case_id="CASE-2",
            document_id="DOC-2",
            doc_hash=self.hash_service.hash_bytes(b"d2"),
            officer_id=self.officer_id,
        )

        checkpoint = self.engine.create_checkpoint()
        proof = self.engine.get_merkle_proof(checkpoint, "CASE-1")

        # Invert position
        inverted_pos = "left" if proof[0]["position"] == "right" else "right"
        corrupted_proof = [{"hash": proof[0]["hash"], "position": inverted_pos}]

        self.assertFalse(
            self.engine.verify_merkle_proof(
                leaf_hash=checkpoint.case_chain_heads["CASE-1"],
                proof=corrupted_proof,
                expected_root=checkpoint.merkle_root,
            )
        )

    def test_get_merkle_proof_case_not_in_checkpoint_raises_error(self) -> None:
        """get_merkle_proof raises MerkleCheckpointError if target case was not included."""
        self.chain_engine.create_genesis(
            case_id="CASE-EXISTING",
            document_id="DOC-1",
            doc_hash=self.hash_service.hash_bytes(b"d1"),
            officer_id=self.officer_id,
        )
        cp = self.engine.create_checkpoint()

        with self.assertRaises(MerkleCheckpointError):
            self.engine.get_merkle_proof(cp, "CASE-NON-EXISTENT")

    # -----------------------------------------------------------------------
    # Multiple Sequential Checkpoints
    # -----------------------------------------------------------------------

    def test_multiple_sequential_checkpoints(self) -> None:
        """Engine maintains history of sequential checkpoints as system state evolves."""
        # 1. Epoch 1: Case A and B
        self.chain_engine.create_genesis(
            case_id="CASE-A",
            document_id="DOC-A1",
            doc_hash=self.hash_service.hash_bytes(b"a1"),
            officer_id=self.officer_id,
        )
        self.chain_engine.create_genesis(
            case_id="CASE-B",
            document_id="DOC-B1",
            doc_hash=self.hash_service.hash_bytes(b"b1"),
            officer_id=self.officer_id,
        )
        cp1 = self.engine.create_checkpoint()

        # 2. Epoch 2: Case C added
        self.chain_engine.create_genesis(
            case_id="CASE-C",
            document_id="DOC-C1",
            doc_hash=self.hash_service.hash_bytes(b"c1"),
            officer_id=self.officer_id,
        )
        cp2 = self.engine.create_checkpoint()

        # 3. Epoch 3: Case A receives new document
        self.chain_engine.append_document(
            case_id="CASE-A",
            document_id="DOC-A2",
            doc_hash=self.hash_service.hash_bytes(b"a2"),
            officer_id=self.officer_id,
        )
        cp3 = self.engine.create_checkpoint()

        # Verify all 3 checkpoints exist and are unique
        checkpoints = self.engine.get_checkpoints()
        self.assertEqual(len(checkpoints), 3)
        self.assertEqual(self.engine.get_latest_checkpoint(), cp3)

        self.assertNotEqual(cp1.merkle_root, cp2.merkle_root)
        self.assertNotEqual(cp2.merkle_root, cp3.merkle_root)


if __name__ == "__main__":
    unittest.main()
