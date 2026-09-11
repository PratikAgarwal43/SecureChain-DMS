"""
SecureChain DMS — Merkle Tree Checkpoint Engine (Module 8)
==========================================================
Global anchoring and cryptographic cross-case checkpoint engine for the
Zero-Trust Digital Evidence Vault (SIH26190).

Legal & Forensic Compliance:
----------------------------
Under Section 65B of the Indian Evidence Act, 1872 and Section 63 of the
Bharatiya Sakshya Adhiniyam (BSA), 2023, electronic evidence must maintain an
auditable chain of custody. In a nationwide judicial system with hundreds of
courts, millions of active cases, and terabytes of evidence, auditing every
individual chain link from genesis on every court query is computationally
prohibitive (O(N * M)).

The Merkle Tree Checkpoint Engine provides:
  1. Global Anchoring: Periodically binds the tip (head_chain_hash) of every active
     case chain into a single 256-bit cryptographic root (Merkle root).
  2. Public / Third-Party Verifiability: The Merkle root can be anchored to
     immutable public gazettes, national eCourts bulletins, or state WORM logs,
     proving that a case's state existed in that exact form at that timestamp.
  3. Efficient Logarithmic Inclusion Proofs (Merkle Proofs):
     An individual case can prove its presence in the global anchor using an O(log K)
     cryptographic proof (where K is the number of cases) without exposing or
     requiring knowledge of any other case's sensitive evidence.
  4. Non-Interference & Privacy: Sibling hashes in a Merkle proof disclose only
     opaque intermediate SHA-256 digests, preserving inter-case confidentiality.

Cryptographic Architecture:
---------------------------
1. Deterministic Case Ordering:
   - Case head hashes are sorted lexicographically by `case_id` before constructing
     the tree. This guarantees that two checkpoints of the identical system state
     always produce identical Merkle roots.

2. Binary Merkle Tree Construction:
   - Leaves = [head_chain_hash_1, head_chain_hash_2, ..., head_chain_hash_K].
   - If a level has an odd number of nodes, the trailing node is duplicated.
   - Pairs are hashed moving upwards: `parent = SHA-256(left + right)`.
   - Root = single 64-character lowercase SHA-256 hex digest.
   - Edge cases:
       - Empty tree (0 cases): returns `GENESIS_HASH` (64 zeros).
       - Single leaf (1 case): returns that case's head_chain_hash directly.

3. Constant-Time Hash Verification:
   - Root comparisons and proof verifications utilize `hmac.compare_digest` to
     prevent timing side-channel attacks.
"""

from __future__ import annotations

import hmac
import logging
import threading
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from securechain_security.chain_engine import (
    ChainEngine,
    ChainError,
    ChainNotFoundError,
)
from securechain_security.hash_service import HashService
from securechain_security.models import (
    GENESIS_HASH,
    MerkleCheckpoint,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Custom Exceptions
# ---------------------------------------------------------------------------


class MerkleCheckpointError(Exception):
    """
    Raised when a Merkle tree calculation, checkpoint creation, or proof operation fails.

    Attributes:
        message: Human-readable error description.
        cause: Underlying caught exception, if applicable.
    """

    def __init__(self, message: str, cause: Optional[Exception] = None) -> None:
        super().__init__(message)
        self.message = message
        self.cause = cause


# ---------------------------------------------------------------------------
# Merkle Checkpoint Engine Implementation
# ---------------------------------------------------------------------------


class MerkleCheckpointEngine:
    """
    Cryptographic Merkle Tree Checkpoint Engine for global anchoring of per-case chains.
    """

    def __init__(
        self,
        chain_engine: ChainEngine,
        hash_service: HashService,
    ) -> None:
        """
        Initialize the MerkleCheckpointEngine with dependency-injected services.

        Args:
            chain_engine: ChainEngine instance managing per-case hash chains.
            hash_service: Stateless SHA-256 cryptographic hashing service.

        Raises:
            MerkleCheckpointError: If chain_engine or hash_service is None.
        """
        if chain_engine is None:
            raise MerkleCheckpointError("chain_engine cannot be None")
        if hash_service is None:
            raise MerkleCheckpointError("hash_service cannot be None")

        self._chain_engine: ChainEngine = chain_engine
        self._hash_service: HashService = hash_service
        self._checkpoints: List[MerkleCheckpoint] = []
        self._lock: threading.RLock = threading.RLock()

        logger.info("MerkleCheckpointEngine initialized successfully")

    @property
    def chain_engine(self) -> ChainEngine:
        """Return the underlying ChainEngine instance."""
        return self._chain_engine

    @property
    def hash_service(self) -> HashService:
        """Return the underlying HashService instance."""
        return self._hash_service

    def _hash_pair(self, left: str, right: str) -> str:
        """
        Cryptographically combine two SHA-256 hex digests: SHA-256(left + right).

        Args:
            left: Left sibling hex digest string.
            right: Right sibling hex digest string.

        Returns:
            64-character lowercase hexadecimal SHA-256 digest.
        """
        payload = f"{left.strip().lower()}{right.strip().lower()}".encode("utf-8")
        return self._hash_service.hash_bytes(payload)

    def _build_tree_nodes(self, leaf_hashes: List[str]) -> List[List[str]]:
        """
        Build and return all levels of the binary Merkle tree from bottom leaves to root.

        Security Rationale:
            Full level node caching is necessary for generating logarithmic Merkle
            inclusion proofs (`get_merkle_proof`). Each level is guaranteed to have
            an even number of nodes (via duplication of trailing odd nodes) except
            the single-element root level.

        Args:
            leaf_hashes: List of 64-char hexadecimal leaf hashes.

        Returns:
            List of levels, where index 0 is the padded leaf level and index -1
            is the single-element root level `[[root]]`.
        """
        if not leaf_hashes:
            return [[]]

        # Clean leaf hashes
        current_level = [str(h).strip().lower() for h in leaf_hashes]

        if len(current_level) == 1:
            return [list(current_level)]

        levels: List[List[str]] = []

        while len(current_level) > 1:
            # If odd number of nodes, duplicate the last leaf/node
            if len(current_level) % 2 == 1:
                current_level.append(current_level[-1])

            levels.append(list(current_level))

            next_level: List[str] = []
            for i in range(0, len(current_level), 2):
                left = current_level[i]
                right = current_level[i + 1]
                parent = self._hash_pair(left, right)
                next_level.append(parent)

            current_level = next_level

        # Append the root level (single node)
        levels.append(list(current_level))
        return levels

    def build_merkle_tree(self, leaf_hashes: List[str]) -> str:
        """
        Build a binary Merkle tree from leaf hashes and return the single Merkle root hash.

        Tree Construction Rules:
          - Empty leaf list: returns `GENESIS_HASH` (64 zeros).
          - Single leaf: returns that leaf hash directly.
          - Odd number of leaves: duplicates the last leaf to maintain binary symmetry.
          - Moving upwards: pairs `(left, right)` are combined as `SHA-256(left + right)`.

        Args:
            leaf_hashes: List of SHA-256 hex string leaves.

        Returns:
            64-character lowercase hexadecimal SHA-256 Merkle root.
        """
        if not leaf_hashes:
            logger.debug("build_merkle_tree: empty leaves, returning GENESIS_HASH")
            return GENESIS_HASH

        if len(leaf_hashes) == 1:
            return leaf_hashes[0].strip().lower()

        levels = self._build_tree_nodes(leaf_hashes)
        root = levels[-1][0]
        logger.debug("build_merkle_tree: computed root %s from %d leaves", root, len(leaf_hashes))
        return root

    def create_checkpoint(self, case_ids: Optional[List[str]] = None) -> MerkleCheckpoint:
        """
        Create and record a global Merkle checkpoint over specified (or all active) cases.

        Execution Lifecycle:
          1. Determines target case IDs (all cases in ChainEngine if case_ids is None).
          2. Sorts case IDs alphabetically for deterministic, reproducible ordering.
          3. Retrieves `head_chain_hash` for each case from its `ChainState`.
          4. Constructs binary Merkle tree from sorted head hashes.
          5. Creates and stores an immutable `MerkleCheckpoint` record.
          6. Returns the checkpoint.

        Args:
            case_ids: Optional explicit list of case IDs to anchor. If None, queries
                      all initialized cases from the chain engine.

        Returns:
            MerkleCheckpoint dataclass instance.

        Raises:
            MerkleCheckpointError: If case data cannot be retrieved or tree build fails.
        """
        with self._lock:
            # Determine cases to include
            if case_ids is None:
                if hasattr(self._chain_engine, "get_all_cases"):
                    target_cases = self._chain_engine.get_all_cases()
                elif hasattr(self._chain_engine, "_chains"):
                    target_cases = list(self._chain_engine._chains.keys())
                else:
                    target_cases = []
            else:
                target_cases = list(case_ids)

            # Sort case IDs alphabetically for strict determinism
            sorted_case_ids = sorted([str(cid).strip() for cid in target_cases if str(cid).strip()])

            case_chain_heads: Dict[str, str] = {}
            leaf_hashes: List[str] = []

            for cid in sorted_case_ids:
                try:
                    state = self._chain_engine.get_chain_state(cid)
                    head_hash = state.head_chain_hash
                except Exception as exc:
                    logger.error("create_checkpoint: failed to retrieve chain state for case '%s': %s", cid, exc)
                    raise MerkleCheckpointError(
                        f"Failed to retrieve chain state for case '{cid}': {exc}", cause=exc
                    ) from exc

                case_chain_heads[cid] = head_hash
                leaf_hashes.append(head_hash)

            # Compute Merkle root
            root = self.build_merkle_tree(leaf_hashes)

            checkpoint = MerkleCheckpoint(
                checkpoint_id=str(uuid.uuid4()),
                merkle_root=root,
                case_chain_heads=case_chain_heads,
                cases_included=len(case_chain_heads),
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

            self._checkpoints.append(checkpoint)

            logger.info(
                "create_checkpoint: created checkpoint '%s' with %d cases (root: %s)",
                checkpoint.checkpoint_id,
                checkpoint.cases_included,
                checkpoint.merkle_root,
            )

            return checkpoint

    def verify_checkpoint(self, checkpoint: MerkleCheckpoint) -> bool:
        """
        Verify that no case chain anchored in a checkpoint has been modified or tampered with.

        Verification Workflow:
          1. Re-fetches the current `head_chain_hash` for each case included in the checkpoint.
          2. Reconstructs the Merkle tree from current head hashes in identical sorted order.
          3. Compares the recomputed root with `checkpoint.merkle_root` using constant-time equality.
          4. Returns True if roots match (chains intact since checkpoint); False if modified.

        Args:
            checkpoint: MerkleCheckpoint instance to verify.

        Returns:
            bool: True if checkpoint is valid and all chains remain intact; False otherwise.
        """
        if not isinstance(checkpoint, MerkleCheckpoint):
            logger.warning("verify_checkpoint: input is not a MerkleCheckpoint instance")
            return False

        sorted_case_ids = sorted(checkpoint.case_chain_heads.keys())
        current_leaf_hashes: List[str] = []

        with self._lock:
            for cid in sorted_case_ids:
                try:
                    current_state = self._chain_engine.get_chain_state(cid)
                    current_leaf_hashes.append(current_state.head_chain_hash)
                except Exception as exc:
                    logger.warning(
                        "verify_checkpoint: failed to get current state for case '%s': %s", cid, exc
                    )
                    return False

        recomputed_root = self.build_merkle_tree(current_leaf_hashes)
        is_valid = hmac.compare_digest(
            recomputed_root.lower().strip(),
            checkpoint.merkle_root.lower().strip(),
        )

        logger.info(
            "verify_checkpoint: checkpoint '%s' verification result: %s",
            checkpoint.checkpoint_id,
            is_valid,
        )
        return is_valid

    def get_merkle_proof(self, checkpoint: MerkleCheckpoint, case_id: str) -> List[Dict[str, str]]:
        """
        Generate a cryptographic Merkle inclusion proof for a specific case within a checkpoint.

        Proof Structure:
            List of sibling hashes and their positions relative to the verification path:
            `[{"hash": "<sibling_hash>", "position": "left" | "right"}, ...]`

        Security Rationale:
            Allows a light client, court registry, or defense advocate to verify that an
            individual case was anchored into the global Merkle root in O(log K) steps,
            without disclosing any details or hashes of unrelated cases in the registry.

        Args:
            checkpoint: MerkleCheckpoint containing the case.
            case_id: Target case identifier to prove.

        Returns:
            List of proof steps from leaf level upwards.

        Raises:
            MerkleCheckpointError: If case_id was not included in the checkpoint.
        """
        if not isinstance(checkpoint, MerkleCheckpoint):
            raise MerkleCheckpointError("Invalid checkpoint: expected MerkleCheckpoint instance")

        clean_case_id = str(case_id).strip()
        if clean_case_id not in checkpoint.case_chain_heads:
            raise MerkleCheckpointError(
                f"Case '{clean_case_id}' was not included in checkpoint '{checkpoint.checkpoint_id}'"
            )

        sorted_case_ids = sorted(checkpoint.case_chain_heads.keys())
        target_index = sorted_case_ids.index(clean_case_id)
        leaf_hashes = [checkpoint.case_chain_heads[cid] for cid in sorted_case_ids]

        if len(leaf_hashes) <= 1:
            # Single leaf or empty tree requires no sibling proof steps
            return []

        levels = self._build_tree_nodes(leaf_hashes)
        proof: List[Dict[str, str]] = []
        idx = target_index

        # Walk through levels except root level (levels[-1])
        for level_idx in range(len(levels) - 1):
            current_level = levels[level_idx]
            if idx % 2 == 0:
                sibling_idx = idx + 1
                pos = "right"
            else:
                sibling_idx = idx - 1
                pos = "left"

            sibling_hash = current_level[sibling_idx]
            proof.append({"hash": sibling_hash, "position": pos})
            idx = idx // 2

        logger.info(
            "get_merkle_proof: generated %d-step proof for case '%s' in checkpoint '%s'",
            len(proof),
            clean_case_id,
            checkpoint.checkpoint_id,
        )
        return proof

    def verify_merkle_proof(
        self,
        leaf_hash: str,
        proof: List[Dict[str, str]],
        expected_root: str,
    ) -> bool:
        """
        Verify a Merkle inclusion proof against an expected root hash using constant-time comparison.

        Verification Algorithm:
          1. Starts with `current_hash = leaf_hash`.
          2. For each step `{"hash": H, "position": P}`:
             - If position == "left": `current_hash = SHA-256(H + current_hash)`.
             - If position == "right": `current_hash = SHA-256(current_hash + H)`.
          3. Verifies `current_hash == expected_root` via `hmac.compare_digest`.

        Args:
            leaf_hash: SHA-256 hash of the target case's head link.
            proof: List of sibling proof steps generated by `get_merkle_proof`.
            expected_root: The expected 64-char Merkle root hash.

        Returns:
            bool: True if proof mathematically reconstructs expected_root; False otherwise.
        """
        if not leaf_hash or not isinstance(leaf_hash, str):
            return False
        if not expected_root or not isinstance(expected_root, str):
            return False
        if not isinstance(proof, list):
            return False

        current_hash = leaf_hash.strip().lower()

        for step in proof:
            if not isinstance(step, dict) or "hash" not in step or "position" not in step:
                logger.warning("verify_merkle_proof: malformed proof step: %s", step)
                return False

            sibling = str(step["hash"]).strip().lower()
            pos = str(step["position"]).strip().lower()

            if pos == "left":
                current_hash = self._hash_pair(sibling, current_hash)
            elif pos == "right":
                current_hash = self._hash_pair(current_hash, sibling)
            else:
                logger.warning("verify_merkle_proof: invalid position '%s'", pos)
                return False

        is_valid = hmac.compare_digest(
            current_hash.lower().strip(),
            expected_root.lower().strip(),
        )

        logger.info("verify_merkle_proof result: %s (computed: %s)", is_valid, current_hash)
        return is_valid

    def get_checkpoints(self) -> List[MerkleCheckpoint]:
        """
        Return a list of all stored checkpoints in chronological order.

        Returns:
            List of MerkleCheckpoint instances.
        """
        with self._lock:
            return list(self._checkpoints)

    def get_latest_checkpoint(self) -> MerkleCheckpoint:
        """
        Return the most recently created MerkleCheckpoint.

        Returns:
            The latest MerkleCheckpoint instance.

        Raises:
            MerkleCheckpointError: If no checkpoints have been created yet.
        """
        with self._lock:
            if not self._checkpoints:
                raise MerkleCheckpointError("No checkpoints have been created yet")
            return self._checkpoints[-1]
