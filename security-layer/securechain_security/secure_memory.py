"""
SecureChain DMS — Secure Memory Handler (Module 9)
===================================================
Zero-Trust memory hygiene module ensuring cryptographic key material (Data
Encryption Keys / DEKs) is reliably scrubbed from RAM after use.

Threat Model & Security Rationale:
----------------------------------
In the Indian Justice System Digital Evidence Vault (SIH26190), evidence
confidentiality and integrity must satisfy stringent forensic and legal
standards under the Bharatiya Sakshya Adhiniyam, 2023 (BSA §63) and the
Information Technology Act, 2000.

1. Crash Dumps & Core Dumps:
   Unhandled exceptions, process crashes, or system panics can trigger the
   operating system to persist the entire userland heap to disk in core dump
   files or Windows Minidump/Memory.dmp files. If DEKs reside unzeroed in
   memory, an adversary with forensic access to the host machine can extract
   the keys and decrypt sealed evidence vaults.

2. Paging & Swap Files:
   Under memory pressure, OS kernels swap memory pages containing sensitive
   process heaps onto unencrypted secondary storage (swap partitions, Linux
   swapfiles, or Windows pagefile.sys). Keys written to swap may persist across
   reboots and system shutdowns on solid-state drives (SSDs) due to wear leveling.

3. CPython Garbage Collection & Immutability:
   Standard Python `bytes` objects are immutable and allocated on the private
   CPython heap. When an immutable `bytes` key goes out of scope, the garbage
   collector merely marks the memory block as free; it NEVER zeroes the
   physical memory contents. The plaintext key lingers in RAM indefinitely until
   overwritten by unrelated allocations.

4. C-Level Zeroing vs Dead-Store Elimination:
   To ensure immediate, deterministic erasure, key material must be held in
   mutable buffers (`bytearray`). Python's `secure_zero` utilizes `ctypes.memset`
   at the C runtime level, bypassing any bytecode or compiler optimizations
   that could elide redundant writes, with a deterministic fallback to ensure
   defense-in-depth across all execution environments.
"""

from __future__ import annotations

import logging
import sys
from typing import Any, Optional, Union

# Import domain constants
from securechain_security.models import DEK_LENGTH_BYTES

# Attempt to load ctypes for C-level memory access
try:
    import ctypes
    import ctypes.util

    _CTYPES_AVAILABLE = True
except ImportError:  # pragma: no cover
    ctypes = None  # type: ignore[assignment]
    _CTYPES_AVAILABLE = False

# Module logger: operational events are logged, but sensitive keys, plaintext,
# and key hashes are NEVER logged.
logger = logging.getLogger("securechain.security.secure_memory")


# ---------------------------------------------------------------------------
# Custom Exceptions
# ---------------------------------------------------------------------------


class SecureMemoryError(Exception):
    """
    Base exception for secure memory management operations.

    Raised when memory zeroing, buffer operations, or key validation fails.
    """


class InvalidKeyLengthError(SecureMemoryError, ValueError):
    """
    Raised when key material fails length validation requirements.

    Inherits from both `SecureMemoryError` and `ValueError` to satisfy
    domain-specific and standard library error handling conventions.
    """


# ---------------------------------------------------------------------------
# Memory Zeroing Primitive
# ---------------------------------------------------------------------------


def secure_zero(buffer: bytearray) -> None:
    """
    Securely overwrite a mutable bytearray with zeros in-place.

    Security Rationale:
    -------------------
    Standard CPython memory management deallocates memory without zeroing,
    leaving plaintext key material exposed in RAM. This function guarantees
    that the memory backing `buffer` is overwritten with null bytes (0x00).

    The function first attempts a C-level memory wipe using `ctypes.memset`.
    Because `memset` operates on the underlying memory address directly via
    the C ABI, it bypasses Python interpreter-level optimizations or dead-store
    elimination. If `ctypes` is unavailable or raises an environment error,
    it falls back to iterative zeroing at the Python level.

    Args:
        buffer: A mutable `bytearray` containing sensitive key material.

    Raises:
        TypeError: If `buffer` is not an instance of `bytearray`.
    """
    if not isinstance(buffer, bytearray):
        raise TypeError(
            f"secure_zero requires a mutable bytearray, received: {type(buffer).__name__}"
        )

    buf_len = len(buffer)
    if buf_len == 0:
        return

    zeroed_c_level = False

    if _CTYPES_AVAILABLE and ctypes is not None:
        try:
            # Obtain a ctypes char array referencing the mutable buffer's address
            c_char_array = (ctypes.c_char * buf_len).from_buffer(buffer)
            ctypes.memset(c_char_array, 0, buf_len)
            zeroed_c_level = True
        except Exception as exc:
            logger.warning(
                "ctypes.memset failed (%s); falling back to Python-level memory wipe",
                exc,
            )

    # Secondary defense-in-depth: overwrite every byte index explicitly
    # to guarantee memory clearing even if ctypes was unavailable or skipped
    for i in range(buf_len):
        buffer[i] = 0

    logger.debug(
        "Securely zeroed buffer (%d bytes) [c_memset=%s]",
        buf_len,
        zeroed_c_level,
    )


# ---------------------------------------------------------------------------
# Memory Locking (Swap Prevention)
# ---------------------------------------------------------------------------


def prevent_swap(buffer: Union[bytearray, memoryview, SecureBuffer]) -> bool:
    """
    Attempt to lock the memory page containing the buffer into physical RAM (mlock).

    Security Rationale:
    -------------------
    Operating systems swap inactive memory pages out to secondary storage (swap
    partitions on Linux, pagefile.sys on Windows). If sensitive cryptographic
    material (DEKs) is paged out, plaintext keys can persist on non-volatile
    disks indefinitely, creating a high-severity forensic exposure risk.

    This function attempts to invoke POSIX `mlock(2)` to pin the memory page into
    physical RAM, forbidding the OS kernel from paging it out to disk.

    Platform Support:
    -----------------
    - Linux: Uses `libc.mlock` via ctypes. Requires appropriate RLIMIT_MEMLOCK
      or CAP_IPC_LOCK privileges. Best-effort: logs a warning if limits are exceeded.
    - Windows / Other: Memory locking is unsupported for arbitrary heap bytearrays
      without specialized VirtualAlloc page-aligned allocations and working-set quota.
      Logs a warning and safely no-ops.

    Args:
        buffer: A `bytearray`, `memoryview`, or `SecureBuffer` instance.

    Returns:
        bool: True if memory locking succeeded; False if unsupported or failed.

    Raises:
        TypeError: If `buffer` is not a bytearray, memoryview, or SecureBuffer.
    """
    if isinstance(buffer, SecureBuffer):
        raw_buffer: Union[bytearray, memoryview] = buffer._buffer
    elif isinstance(buffer, (bytearray, memoryview)):
        raw_buffer = buffer
    else:
        raise TypeError(
            f"prevent_swap requires bytearray, memoryview, or SecureBuffer, "
            f"received: {type(buffer).__name__}"
        )

    buf_len = len(raw_buffer)
    if buf_len == 0:
        return True

    if not _CTYPES_AVAILABLE or ctypes is None:
        logger.warning(
            "ctypes unavailable; cannot invoke mlock for memory swap prevention"
        )
        return False

    if sys.platform.startswith("linux"):
        try:
            libc_name = ctypes.util.find_library("c") or "libc.so.6"
            libc = ctypes.CDLL(libc_name, use_errno=True)
            if hasattr(libc, "mlock"):
                c_char_array = (ctypes.c_char * buf_len).from_buffer(raw_buffer)
                addr = ctypes.addressof(c_char_array)
                res = libc.mlock(ctypes.c_void_p(addr), ctypes.c_size_t(buf_len))
                if res != 0:
                    errno_val = ctypes.get_errno()
                    logger.warning(
                        "mlock failed with errno %d (RLIMIT_MEMLOCK exceeded or insufficient privileges); "
                        "swap prevention is inactive",
                        errno_val,
                    )
                    return False
                logger.debug("Successfully locked %d bytes into RAM via mlock", buf_len)
                return True
            logger.warning(
                "POSIX mlock symbol not found in libc; memory swap prevention inactive"
            )
            return False
        except Exception as exc:
            logger.warning("Unexpected error attempting mlock on Linux: %s", exc)
            return False

    # Windows and other unsupported platforms
    logger.warning(
        "Memory locking (prevent_swap) is not supported on platform '%s'; "
        "memory swap protection is best-effort and inactive",
        sys.platform,
    )
    return False


def unlock_memory(buffer: Union[bytearray, memoryview, SecureBuffer]) -> bool:
    """
    Attempt to unlock memory previously locked with prevent_swap (munlock).

    Complementary helper for `prevent_swap` to release memory lock limits
    after key lifecycle completion.

    Args:
        buffer: A `bytearray`, `memoryview`, or `SecureBuffer` instance.

    Returns:
        bool: True if memory unlock succeeded; False if unsupported or failed.

    Raises:
        TypeError: If `buffer` is not a bytearray, memoryview, or SecureBuffer.
    """
    if isinstance(buffer, SecureBuffer):
        raw_buffer: Union[bytearray, memoryview] = buffer._buffer
    elif isinstance(buffer, (bytearray, memoryview)):
        raw_buffer = buffer
    else:
        raise TypeError(
            f"unlock_memory requires bytearray, memoryview, or SecureBuffer, "
            f"received: {type(buffer).__name__}"
        )

    buf_len = len(raw_buffer)
    if buf_len == 0:
        return True

    if not _CTYPES_AVAILABLE or ctypes is None:
        return False

    if sys.platform.startswith("linux"):
        try:
            libc_name = ctypes.util.find_library("c") or "libc.so.6"
            libc = ctypes.CDLL(libc_name, use_errno=True)
            if hasattr(libc, "munlock"):
                c_char_array = (ctypes.c_char * buf_len).from_buffer(raw_buffer)
                addr = ctypes.addressof(c_char_array)
                res = libc.munlock(ctypes.c_void_p(addr), ctypes.c_size_t(buf_len))
                if res != 0:
                    errno_val = ctypes.get_errno()
                    logger.warning("munlock failed with errno %d", errno_val)
                    return False
                logger.debug("Successfully unlocked %d bytes from RAM", buf_len)
                return True
        except Exception as exc:
            logger.warning("Unexpected error during munlock on Linux: %s", exc)
            return False

    return False


# ---------------------------------------------------------------------------
# SecureBuffer Context Manager
# ---------------------------------------------------------------------------


class SecureBuffer:
    """
    A context manager wrapping sensitive key material in a mutable bytearray.

    Security Rationale:
    -------------------
    Provides deterministic cleanup for cryptographic keys. When entering the
    context, returns the mutable `bytearray` containing the key bytes so that
    cryptographic ciphers (e.g. `AESGCM(key)`) can execute directly. Upon exiting
    the context, `secure_zero` is automatically invoked to wipe the buffer memory
    with zeros at the C level.

    As a safety net, `__del__` is implemented to trigger memory zeroing if the
    object is garbage collected outside an explicit context block.

    Example:
        >>> from securechain_security.secure_memory import SecureBuffer
        >>> with SecureBuffer(b"\\x01" * 32) as key_buf:
        ...     # Use key_buf for encryption
        ...     assert len(key_buf) == 32
        >>> # key_buf is now completely zeroed in memory
        >>> assert all(b == 0 for b in key_buf)
    """

    def __init__(
        self,
        data: Union[bytes, bytearray, memoryview],
        lock_memory: bool = False,
    ) -> None:
        """
        Initialize the secure buffer by copying input bytes into a mutable bytearray.

        Args:
            data: Bytes-like key material to securely wrap.
            lock_memory: If True, attempts to lock the memory page into RAM via
                `prevent_swap` (best-effort). Default is False.

        Raises:
            TypeError: If `data` is not a bytes-like object.
        """
        if not isinstance(data, (bytes, bytearray, memoryview)):
            raise TypeError(
                f"SecureBuffer requires bytes-like data, received: {type(data).__name__}"
            )

        self._buffer: bytearray = bytearray(data)
        self._is_wiped: bool = False
        self._initial_len: int = len(self._buffer)
        self._is_locked: bool = False

        if lock_memory and self._initial_len > 0:
            self._is_locked = prevent_swap(self._buffer)

        logger.debug(
            "SecureBuffer allocated (%d bytes, locked=%s)",
            self._initial_len,
            self._is_locked,
        )

    @property
    def data(self) -> bytes:
        """
        Return the current buffer contents as an immutable bytes copy.

        Security Note:
        --------------
        This returns a snapshot copy. If the buffer has been zeroed, this
        property returns a bytes object consisting of all zeros.

        Returns:
            bytes: Immutable copy of current buffer content.
        """
        return bytes(self._buffer)

    @property
    def is_wiped(self) -> bool:
        """
        Return True if the internal buffer has already been zeroed.

        Returns:
            bool: True if wiped, False if still holding active key material.
        """
        return self._is_wiped

    def wipe(self) -> None:
        """
        Explicitly zero the internal memory buffer and mark as wiped.

        Idempotent: Safe to invoke multiple times without error.
        """
        if not self._is_wiped:
            if self._is_locked:
                unlock_memory(self._buffer)
                self._is_locked = False
            secure_zero(self._buffer)
            self._is_wiped = True
            logger.debug(
                "SecureBuffer wiped successfully (%d bytes scrubbed)",
                self._initial_len,
            )

    def __enter__(self) -> bytearray:
        """
        Enter runtime context.

        Returns:
            bytearray: The mutable bytearray holding key material.

        Raises:
            SecureMemoryError: If the buffer has already been zeroed.
        """
        if self._is_wiped:
            raise SecureMemoryError(
                "Cannot enter context: SecureBuffer has already been zeroed."
            )
        return self._buffer

    def __exit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[Any],
    ) -> None:
        """
        Exit runtime context and reliably wipe buffer from memory.
        """
        self.wipe()

    def __del__(self) -> None:
        """
        Safety net destructor: wipe buffer if garbage collected without context exit.
        """
        try:
            if hasattr(self, "_is_wiped") and not self._is_wiped:
                self.wipe()
        except Exception:
            # Destructors must suppress exceptions during interpreter teardown
            pass

    def __len__(self) -> int:
        """Return the current length of the buffer in bytes."""
        return len(self._buffer)

    def __repr__(self) -> str:
        """
        Return a safe representation that never leaks key material.
        """
        status = "wiped" if self._is_wiped else "active"
        return f"<SecureBuffer len={len(self._buffer)} status={status}>"

    def __str__(self) -> str:
        """Return string representation identical to __repr__."""
        return self.__repr__()


# ---------------------------------------------------------------------------
# Convenience Functions
# ---------------------------------------------------------------------------


def secure_dek_context(
    dek: Union[bytes, bytearray, memoryview],
    lock_memory: bool = False,
) -> SecureBuffer:
    """
    Convenience function returning a SecureBuffer context manager for a DEK.

    Validates that the provided Data Encryption Key (DEK) is exactly
    `DEK_LENGTH_BYTES` (32 bytes / 256 bits) as required for AES-256-GCM
    envelope encryption in the SecureChain DMS Two-Vault architecture.

    Args:
        dek: Raw 32-byte Data Encryption Key.
        lock_memory: If True, attempts to prevent memory paging to disk (best-effort).

    Returns:
        SecureBuffer: A context manager wrapping the validated DEK.

    Raises:
        TypeError: If `dek` is not a bytes-like object.
        InvalidKeyLengthError: If `dek` is not exactly 32 bytes (256 bits).

    Example:
        >>> with secure_dek_context(raw_dek_32_bytes) as dek_buf:
        ...     cipher = AESGCM(dek_buf)
        ...     ciphertext = cipher.encrypt(iv, plaintext, aad)
        >>> # dek_buf is now wiped
    """
    if not isinstance(dek, (bytes, bytearray, memoryview)):
        raise TypeError(
            f"DEK must be bytes-like, received: {type(dek).__name__}"
        )

    actual_len = len(dek)
    if actual_len != DEK_LENGTH_BYTES:
        raise InvalidKeyLengthError(
            f"Invalid DEK length: expected {DEK_LENGTH_BYTES} bytes (256 bits), "
            f"received {actual_len} bytes"
        )

    logger.debug("Created secure DEK context for %d-byte key", actual_len)
    return SecureBuffer(dek, lock_memory=lock_memory)
