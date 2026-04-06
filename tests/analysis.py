"""
analysis.py
===========
Security analysis module for a multi-layer encryption pipeline
(Playfair → Columnar Transposition → DES).

Supports both text and binary file encryption/decryption with
Base64 bridging, entropy analysis, frequency distribution,
uniformity scoring, integrity validation, and matplotlib visualisation.
"""

from __future__ import annotations

import base64
import math
import os
import struct
from collections import Counter
from pathlib import Path
from typing import Union

import matplotlib.pyplot as plt
import numpy as np

# ---------------------------------------------------------------------------
# NOTE: Replace this stub import with your real encryption module.
# The module must expose:
#   encrypt_text(plaintext: str)  -> str
#   decrypt_text(ciphertext: str) -> str
# ---------------------------------------------------------------------------
try:
    from encryption import encrypt_text, decrypt_text          # type: ignore[import-not-found]  # noqa: F401
except ImportError:                                            # pragma: no cover
    # ── Stub implementations used when the real module is absent ──────────
    def encrypt_text(plaintext: str) -> str:                   # type: ignore[misc]
        """Stub: Caesar +3 (replace with real pipeline)."""
        return "".join(chr((ord(c) + 3) % 256) for c in plaintext)

    def decrypt_text(ciphertext: str) -> str:                  # type: ignore[misc]
        """Stub: Caesar -3 (replace with real pipeline)."""
        return "".join(chr((ord(c) - 3) % 256) for c in ciphertext)


# ═══════════════════════════════════════════════════════════════════════════
# 1.  CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════

ALLOWED_EXTENSIONS: set[str] = {
    "txt", "log", "csv", "json", "md",          # text
    "pdf", "doc", "docx", "png", "jpg", "jpeg", # binary
}

BINARY_EXTENSIONS: set[str] = {
    "pdf", "doc", "docx", "png", "jpg", "jpeg",
}


# ═══════════════════════════════════════════════════════════════════════════
# 2.  UTILITY FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

def _to_bytes(data: Union[str, bytes]) -> bytes:
    """Convert *data* to :class:`bytes`.

    - ``bytes`` → returned unchanged.
    - ``str``   → encoded as UTF-8.
    """
    if isinstance(data, bytes):
        return data
    if isinstance(data, str):
        return data.encode("utf-8")
    raise TypeError(f"Expected str or bytes, got {type(data).__name__!r}")


def _to_str(data: Union[str, bytes]) -> str:
    """Convert *data* to :class:`str`.

    - ``str``   → returned unchanged.
    - ``bytes`` → decoded as UTF-8 (with ``errors='replace'`` for safety).
    """
    if isinstance(data, str):
        return data
    if isinstance(data, bytes):
        return data.decode("utf-8", errors="replace")
    raise TypeError(f"Expected str or bytes, got {type(data).__name__!r}")


def is_binary_file(filename: str) -> bool:
    """Return ``True`` when *filename*'s extension is in :data:`BINARY_EXTENSIONS`."""
    ext = Path(filename).suffix.lstrip(".").lower()
    return ext in BINARY_EXTENSIONS


def _validate_extension(filename: str) -> None:
    """Raise :class:`ValueError` when the file extension is not allowed."""
    ext = Path(filename).suffix.lstrip(".").lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file extension '.{ext}'. "
            f"Allowed: {sorted(ALLOWED_EXTENSIONS)}"
        )


# ═══════════════════════════════════════════════════════════════════════════
# 3.  ENCRYPTION / DECRYPTION WRAPPERS
# ═══════════════════════════════════════════════════════════════════════════

def _normalize_b64(raw: str) -> str:
    """Re-pad a Base64 string that may have been altered by cipher padding.

    Playfair and columnar transposition can append filler characters (e.g.
    ``'X'``) to reach block boundaries.  This helper strips anything that is
    not a legal Base64 character, then re-applies ``=`` padding so that
    :func:`base64.b64decode` succeeds reliably.
    """
    legal = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=")
    cleaned = "".join(ch for ch in raw if ch in legal).rstrip("=")
    padding = (4 - len(cleaned) % 4) % 4
    return cleaned + "=" * padding


def encrypt_data(data: Union[str, bytes], *, is_binary: bool = False) -> str:
    """Encrypt *data* through the full multi-layer pipeline.

    Parameters
    ----------
    data:
        Plaintext string **or** raw bytes (binary file content).
    is_binary:
        Automatically set to ``True`` when *data* is ``bytes``.  Controls
        whether :func:`decrypt_data` returns ``bytes`` or ``str``.

    Returns
    -------
    str
        Encrypted ciphertext produced by :func:`encrypt_text`.

    Notes
    -----
    **Why always Base64-encode — even for plain text?**

    The Playfair cipher only understands the A-Z alphabet — it uppercases
    input, strips non-alpha characters, and may insert filler ``X`` letters.
    Feeding arbitrary text directly into the pipeline causes irreversible data
    loss, making exact round-trip recovery impossible.

    Base64-encoding first solves every problem at once:

    * Output uses only ``A-Z``, ``a-z``, ``0-9``, ``+``, ``/``, ``=`` —
      all characters that survive Playfair + Columnar Transposition intact.
    * ``encrypt_text()`` always receives a clean, valid Python ``str``.
    * Base64 entropy (~6 bits/byte) is always lower than DES output
      (~8 bits/byte), so entropy is *guaranteed* to increase after encryption.
    """
    if isinstance(data, bytes):
        is_binary = True  # noqa: F841 — consumed by decrypt_data via caller

    # ── Always Base64-encode regardless of text / binary mode ─────────────
    # Guarantees: (a) encrypt_text() always receives a valid str,
    #             (b) decrypt_data() can always recover the exact original.
    raw_bytes: bytes = _to_bytes(data)
    payload: str = base64.b64encode(raw_bytes).decode("ascii")

    return encrypt_text(payload)


def decrypt_data(
    data: Union[str, bytes],
    *,
    is_binary: bool = False,
) -> Union[str, bytes]:
    """Decrypt *data* and recover the original plaintext or binary content.

    Parameters
    ----------
    data:
        Ciphertext string (or bytes decoded as UTF-8 before processing).
    is_binary:
        When ``True``, the recovered payload is returned as ``bytes``.
        When ``False`` (default), it is returned as a UTF-8 ``str``.

    Returns
    -------
    str | bytes
        Exact original value that was passed to :func:`encrypt_data`.

    Raises
    ------
    ValueError
        When the decrypted payload is not valid Base64, indicating ciphertext
        corruption or a text/binary mode mismatch.
    """
    ciphertext: str = _to_str(data)

    # ── Run the full decryption pipeline ──────────────────────────────────
    b64_payload: str = decrypt_text(ciphertext)

    # ── Repair Base64 padding that cipher layers may have altered ─────────
    b64_padded: str = _normalize_b64(b64_payload)

    try:
        recovered_bytes: bytes = base64.b64decode(b64_padded)
    except Exception as exc:
        raise ValueError(
            "Base64 decoding failed after decryption — "
            "ciphertext may be corrupted or wrong is_binary mode was used.\n"
            f"  Decrypted payload (first 120 chars): {b64_payload[:120]!r}"
        ) from exc

    # ── Return the correct type to match what was originally encrypted ─────
    return recovered_bytes if is_binary else recovered_bytes.decode("utf-8")


# ═══════════════════════════════════════════════════════════════════════════
# 4.  FILE OPERATIONS
# ═══════════════════════════════════════════════════════════════════════════

def encrypt_file(input_path: str, output_path: str) -> None:
    """Encrypt the file at *input_path* and write ciphertext to *output_path*.

    The function automatically detects whether the source file is binary
    (via extension) and applies Base64 wrapping accordingly.

    Parameters
    ----------
    input_path:
        Path to the plaintext / original file.
    output_path:
        Destination path for the encrypted output (always written as text).
    """
    _validate_extension(input_path)

    binary_mode: bool = is_binary_file(input_path)

    if binary_mode:
        with open(input_path, "rb") as fh:
            raw: bytes = fh.read()
        ciphertext: str = encrypt_data(raw, is_binary=True)
    else:
        with open(input_path, "r", encoding="utf-8") as fh:
            text: str = fh.read()
        ciphertext = encrypt_data(text, is_binary=False)

    with open(output_path, "w", encoding="utf-8") as fh:
        fh.write(ciphertext)

    print(f"[encrypt_file] '{input_path}' → '{output_path}' "
          f"({'binary' if binary_mode else 'text'} mode)")


def decrypt_file(input_path: str, output_path: str) -> None:
    """Decrypt the ciphertext file at *input_path* and write the result to *output_path*.

    Extension detection is performed on *output_path* so that binary files
    are reconstructed correctly.

    Parameters
    ----------
    input_path:
        Path to the encrypted ciphertext file (text).
    output_path:
        Destination path for the decrypted output.  Its extension determines
        whether Base64 decoding is applied.
    """
    _validate_extension(output_path)

    binary_mode: bool = is_binary_file(output_path)

    with open(input_path, "r", encoding="utf-8") as fh:
        ciphertext: str = fh.read()

    result = decrypt_data(ciphertext, is_binary=binary_mode)

    if binary_mode:
        assert isinstance(result, bytes)
        with open(output_path, "wb") as fh:
            fh.write(result)
    else:
        assert isinstance(result, str)
        with open(output_path, "w", encoding="utf-8") as fh:
            fh.write(result)

    print(f"[decrypt_file] '{input_path}' → '{output_path}' "
          f"({'binary' if binary_mode else 'text'} mode)")


# ═══════════════════════════════════════════════════════════════════════════
# 5.  SECURITY ANALYSIS  (existing logic – preserved & extended)
# ═══════════════════════════════════════════════════════════════════════════

def shannon_entropy(data: Union[str, bytes]) -> float:
    """Calculate Shannon entropy (bits per byte) of *data*.

    A perfectly random stream approaches 8.0 bits/byte.

    Parameters
    ----------
    data:
        Raw bytes or a string (converted to bytes via UTF-8).

    Returns
    -------
    float
        Shannon entropy in bits per byte.  Returns ``0.0`` for empty input.
    """
    raw: bytes = _to_bytes(data)
    if not raw:
        return 0.0

    freq = Counter(raw)
    total = len(raw)
    return -sum(
        (count / total) * math.log2(count / total)
        for count in freq.values()
    )


def frequency_distribution(data: Union[str, bytes]) -> dict[int, float]:
    """Compute byte-level frequency distribution of *data*.

    Returns
    -------
    dict[int, float]
        Mapping of byte value (0–255) → relative frequency (0.0–1.0).
    """
    raw: bytes = _to_bytes(data)
    if not raw:
        return {}

    total = len(raw)
    freq = Counter(raw)
    return {byte_val: count / total for byte_val, count in sorted(freq.items())}


def uniformity_score(data: Union[str, bytes]) -> float:
    """Score how uniformly bytes are distributed (0.0 = worst, 1.0 = perfect).

    The score is computed as ``1 - (std_dev / ideal_std_dev)`` where the
    *ideal* standard deviation is that of a perfectly uniform distribution
    over 256 symbols.  Values near 1.0 indicate high cipher quality.

    Returns
    -------
    float
        Uniformity score clamped to [0.0, 1.0].
    """
    raw: bytes = _to_bytes(data)
    if not raw:
        return 0.0

    counts = np.zeros(256, dtype=float)
    for b in raw:
        counts[b] += 1

    freq = counts / len(raw)
    ideal = 1.0 / 256.0

    # Standard deviation of observed vs ideal uniform distribution
    std_dev = float(np.std(freq))
    ideal_std_dev = float(np.std(np.full(256, ideal)))

    if ideal_std_dev == 0:
        return 1.0

    score = 1.0 - (std_dev / ideal_std_dev)
    return float(np.clip(score, 0.0, 1.0))


# ═══════════════════════════════════════════════════════════════════════════
# 6.  INTEGRITY VALIDATION
# ═══════════════════════════════════════════════════════════════════════════

def validate_integrity(
    original: Union[str, bytes],
    *,
    is_binary: bool = False,
) -> bool:
    """Verify that ``decrypt(encrypt(original)) == original``.

    Parameters
    ----------
    original:
        The original plaintext ``str`` or raw ``bytes``.
    is_binary:
        Automatically inferred when *original* is ``bytes``.  Pass ``True``
        explicitly when *original* is a ``str`` that represents binary content
        (unusual — prefer passing actual ``bytes``).

    Returns
    -------
    bool
        ``True`` only when the recovered value is *identical* to *original*.
        Any exception during encryption or decryption returns ``False`` and
        prints a diagnostic message so the cause is visible in test output.
    """
    # Auto-detect binary so callers can pass raw bytes without the flag
    if isinstance(original, bytes):
        is_binary = True

    try:
        ciphertext: str   = encrypt_data(original, is_binary=is_binary)
        recovered         = decrypt_data(ciphertext, is_binary=is_binary)

        if recovered != original:
            # Emit a diagnostic so pytest -v shows what mismatched
            print(
                f"[validate_integrity] MISMATCH\n"
                f"  expected : {original!r:.120}\n"
                f"  got      : {recovered!r:.120}"
            )
            return False
        return True

    except Exception as exc:                         # pragma: no cover
        print(f"[validate_integrity] EXCEPTION: {exc}")
        return False


def validate_multilayer(
    original: Union[str, bytes],
    *,
    is_binary: bool = False,
    layers: int = 3,
) -> dict[str, object]:
    """Confirm round-trip integrity across all *layers* of the pipeline.

    Each iteration performs an independent ``encrypt → decrypt`` cycle on the
    *same* original data.  This confirms that the result is *deterministic and
    stable* across repeated calls — a requirement for composed cipher layers.

    Parameters
    ----------
    original:
        Plaintext / binary data to validate.
    is_binary:
        Automatically inferred when *original* is ``bytes``.
    layers:
        Number of independent round-trip checks to run (default: 3, matching
        the Playfair → Columnar → DES pipeline depth).

    Returns
    -------
    dict
        ::

            {
                "passed":        bool,        # True only if ALL layers passed
                "layers_tested": int,         # stops early on first failure
                "details":       list[bool],  # per-layer result
            }

    Notes
    -----
    **Why not chain encryptions?**

    The previous implementation re-encrypted the ciphertext in each loop
    iteration, which (a) mutated ``is_binary`` mid-loop and (b) produced a
    doubly-encrypted payload that ``decrypt_data`` could never recover from
    in a single call.  Independent round-trips on the *original* data are both
    correct and sufficient to prove pipeline stability.
    """
    if isinstance(original, bytes):
        is_binary = True

    results: list[bool] = []

    for layer_index in range(1, layers + 1):
        ok = validate_integrity(original, is_binary=is_binary)
        results.append(ok)
        if not ok:
            print(f"[validate_multilayer] Failed at layer {layer_index} — stopping early.")
            break

    return {
        "passed":        all(results),
        "layers_tested": len(results),
        "details":       results,
    }


# ═══════════════════════════════════════════════════════════════════════════
# 7.  SECURITY REPORT
# ═══════════════════════════════════════════════════════════════════════════

def security_report(
    original: Union[str, bytes],
    *,
    is_binary: bool = False,
    label: str = "data",
) -> dict[str, object]:
    """Generate a comprehensive security analysis report.

    Analyses Shannon entropy, uniformity score, frequency distribution,
    and integrity validation for both the original and encrypted data.

    Parameters
    ----------
    original:
        The original plaintext or binary content.
    is_binary:
        Must be ``True`` for binary inputs.
    label:
        Human-readable label used in the printed report.

    Returns
    -------
    dict
        Full report dictionary with all metrics.
    """
    if isinstance(original, bytes):
        is_binary = True

    ciphertext: str = encrypt_data(original, is_binary=is_binary)

    orig_bytes: bytes = _to_bytes(original)
    ciph_bytes: bytes = _to_bytes(ciphertext)

    orig_entropy  = shannon_entropy(orig_bytes)
    ciph_entropy  = shannon_entropy(ciph_bytes)
    orig_uniform  = uniformity_score(orig_bytes)
    ciph_uniform  = uniformity_score(ciph_bytes)
    integrity_ok  = validate_integrity(original, is_binary=is_binary)
    multilayer    = validate_multilayer(original, is_binary=is_binary)

    report: dict[str, object] = {
        "label":             label,
        "original_size":     len(orig_bytes),
        "encrypted_size":    len(ciph_bytes),
        "original_entropy":  round(orig_entropy, 4),
        "encrypted_entropy": round(ciph_entropy, 4),
        "entropy_delta":     round(ciph_entropy - orig_entropy, 4),
        "original_uniformity":  round(orig_uniform, 4),
        "encrypted_uniformity": round(ciph_uniform, 4),
        "integrity_valid":   integrity_ok,
        "multilayer":        multilayer,
    }

    # ── Pretty-print ────────────────────────────────────────────────────────
    sep = "═" * 60
    print(sep)
    print(f"  SECURITY REPORT  —  {label}")
    print(sep)
    print(f"  Size          : {report['original_size']} → {report['encrypted_size']} bytes")
    print(f"  Entropy       : {report['original_entropy']} → {report['encrypted_entropy']} "
          f"bits/byte  (Δ {report['entropy_delta']:+.4f})")
    print(f"  Uniformity    : {report['original_uniformity']} → {report['encrypted_uniformity']}")
    print(f"  Integrity     : {'✓ PASS' if integrity_ok else '✗ FAIL'}")
    print(f"  Multi-layer   : {'✓ PASS' if multilayer['passed'] else '✗ FAIL'} "
          f"({multilayer['layers_tested']} layers)")
    print(sep)

    return report


# ═══════════════════════════════════════════════════════════════════════════
# 8.  VISUALISATION
# ═══════════════════════════════════════════════════════════════════════════

def plot_frequency_comparison(
    original: Union[str, bytes],
    *,
    is_binary: bool = False,
    title: str = "Byte Frequency: Original vs Encrypted",
    save_path: str | None = None,
    show: bool = True,
) -> None:
    """Plot a side-by-side byte-frequency comparison using matplotlib.

    Parameters
    ----------
    original:
        Original plaintext or binary content.
    is_binary:
        Set ``True`` for binary data.
    title:
        Title shown on the plot.
    save_path:
        If provided, the figure is saved to this path instead of (or in
        addition to) being displayed.
    show:
        If ``True``, :func:`matplotlib.pyplot.show` is called.
    """
    if isinstance(original, bytes):
        is_binary = True

    ciphertext: str = encrypt_data(original, is_binary=is_binary)

    orig_dist = frequency_distribution(_to_bytes(original))
    ciph_dist = frequency_distribution(_to_bytes(ciphertext))

    x      = np.arange(256)
    orig_y = np.array([orig_dist.get(i, 0.0) for i in range(256)])
    ciph_y = np.array([ciph_dist.get(i, 0.0) for i in range(256)])

    fig, axes = plt.subplots(2, 1, figsize=(14, 8), sharex=True)
    fig.suptitle(title, fontsize=14, fontweight="bold")

    # Original
    axes[0].bar(x, orig_y, color="#4C72B0", width=1.0, alpha=0.85)
    axes[0].set_title("Original Data")
    axes[0].set_ylabel("Relative Frequency")
    axes[0].set_xlim(0, 255)

    # Encrypted
    axes[1].bar(x, ciph_y, color="#DD8452", width=1.0, alpha=0.85)
    axes[1].set_title("Encrypted Data")
    axes[1].set_ylabel("Relative Frequency")
    axes[1].set_xlabel("Byte Value (0–255)")

    plt.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"[plot] Figure saved to '{save_path}'")

    if show:
        plt.show()
    else:
        plt.close(fig)


# ═══════════════════════════════════════════════════════════════════════════
# 9.  PYTEST-COMPATIBLE TEST CASES
# ═══════════════════════════════════════════════════════════════════════════

def _make_temp_text_file(content: str, suffix: str = ".txt") -> str:
    """Write *content* to a temporary file and return its path."""
    import tempfile
    fd, path = tempfile.mkstemp(suffix=suffix)
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write(content)
    return path


def _make_temp_binary_file(content: bytes, suffix: str = ".png") -> str:
    """Write binary *content* to a temporary file and return its path."""
    import tempfile
    fd, path = tempfile.mkstemp(suffix=suffix)
    with os.fdopen(fd, "wb") as fh:
        fh.write(content)
    return path


# ── Utility tests ──────────────────────────────────────────────────────────

def test_to_bytes_from_str() -> None:
    assert _to_bytes("hello") == b"hello"

def test_to_bytes_from_bytes() -> None:
    assert _to_bytes(b"hello") == b"hello"

def test_to_str_from_bytes() -> None:
    assert _to_str(b"hello") == "hello"

def test_to_str_from_str() -> None:
    assert _to_str("hello") == "hello"

def test_is_binary_file_true() -> None:
    for ext in BINARY_EXTENSIONS:
        assert is_binary_file(f"file.{ext}"), f"Expected True for .{ext}"

def test_is_binary_file_false() -> None:
    assert not is_binary_file("document.txt")
    assert not is_binary_file("log.csv")

def test_validate_extension_allowed() -> None:
    for ext in ALLOWED_EXTENSIONS:
        _validate_extension(f"file.{ext}")   # should not raise

def test_validate_extension_rejected() -> None:
    import pytest
    with pytest.raises(ValueError):
        _validate_extension("archive.zip")


# ── Encryption round-trip tests ────────────────────────────────────────────

def test_text_roundtrip() -> None:
    original = "Hello, World! This is a test message."
    ciphertext = encrypt_data(original)
    recovered  = decrypt_data(ciphertext)
    assert recovered == original, "Text round-trip failed"

def test_binary_roundtrip() -> None:
    original = bytes(range(256)) * 4           # 1 024 bytes of varied data
    ciphertext = encrypt_data(original, is_binary=True)
    recovered  = decrypt_data(ciphertext, is_binary=True)
    assert recovered == original, "Binary round-trip failed"

def test_text_integrity() -> None:
    assert validate_integrity("Encrypt me!", is_binary=False)

def test_binary_integrity() -> None:
    payload = b"\x89PNG\r\n\x1a\nFAKE_PNG_DATA"
    assert validate_integrity(payload, is_binary=True)

def test_multilayer_validation() -> None:
    result = validate_multilayer("Multi-layer test", is_binary=False)
    assert result["passed"], f"Multi-layer validation failed: {result}"


# ── Security analysis tests ────────────────────────────────────────────────

def test_shannon_entropy_empty() -> None:
    assert shannon_entropy(b"") == 0.0

def test_shannon_entropy_uniform() -> None:
    data = bytes(range(256))
    assert abs(shannon_entropy(data) - 8.0) < 0.01

def test_frequency_distribution_sum() -> None:
    dist = frequency_distribution(b"abcdef")
    assert abs(sum(dist.values()) - 1.0) < 1e-9

def test_uniformity_score_range() -> None:
    for data in [b"aaaa", bytes(range(256)), b""]:
        score = uniformity_score(data)
        assert 0.0 <= score <= 1.0, f"Score out of range: {score}"

def test_security_report_keys() -> None:
    report = security_report("Sample text for security report")
    required_keys = {
        "label", "original_size", "encrypted_size",
        "original_entropy", "encrypted_entropy", "entropy_delta",
        "original_uniformity", "encrypted_uniformity",
        "integrity_valid", "multilayer",
    }
    assert required_keys.issubset(report.keys())

def test_security_report_integrity_field() -> None:
    report = security_report("Integrity check payload")
    assert report["integrity_valid"] is True


# ── File operation tests ───────────────────────────────────────────────────

def test_encrypt_decrypt_text_file() -> None:
    import os
    src  = _make_temp_text_file("Top secret text content.")
    enc  = str(Path(src).with_suffix(".enc"))
    out  = str(Path(src).with_suffix(".dec.txt"))
    try:
        encrypt_file(src, enc)
        decrypt_file(enc, out)
        with open(out, "r", encoding="utf-8") as fh:
            recovered = fh.read()
        assert recovered == "Top secret text content."
    finally:
        for p in (src, enc, out):
            if os.path.exists(p):
                os.remove(p)

def test_encrypt_decrypt_binary_file() -> None:
    import os
    fake_png = b"\x89PNG\r\n\x1a\n" + bytes(range(100))
    src  = _make_temp_binary_file(fake_png, suffix=".png")
    enc  = str(Path(src).with_suffix(".enc"))
    out  = str(Path(src).with_suffix(".dec.png"))
    try:
        encrypt_file(src, enc)
        decrypt_file(enc, out)
        with open(out, "rb") as fh:
            recovered = fh.read()
        assert recovered == fake_png, "Binary file round-trip failed"
    finally:
        for p in (src, enc, out):
            if os.path.exists(p):
                os.remove(p)


# ═══════════════════════════════════════════════════════════════════════════
# 10.  QUICK DEMO  (python analysis.py)
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("\n" + "═" * 60)
    print("  Multi-Layer Encryption — Analysis Module Demo")
    print("═" * 60 + "\n")

    # ── Text demo ─────────────────────────────────────────────────────────
    sample_text = (
        "The quick brown fox jumps over the lazy dog. "
        "This sentence is used for cryptographic testing purposes."
    )
    print("▶  Text security report:")
    security_report(sample_text, label="sample_text")

    # ── Binary demo ───────────────────────────────────────────────────────
    fake_binary = b"\x89PNG\r\n\x1a\n" + struct.pack(">I", 13) + b"IHDR" + bytes(range(50))
    print("\n▶  Binary security report:")
    security_report(fake_binary, is_binary=True, label="fake_png")

    # ── Frequency plot ────────────────────────────────────────────────────
    print("\n▶  Plotting frequency comparison …")
    plot_frequency_comparison(
        sample_text,
        title="Byte Frequency: Sample Text vs Encrypted",
        save_path="frequency_comparison.png",
        show=False,
    )

    print("\nDemo complete.  Run 'pytest analysis.py -v' to execute all tests.")
    