"""
backend/keys.py  –  System-managed key store for the 3-layer encryption pipeline.

Keys are generated ONCE via `python -m backend.keys --init` and persisted to
.keys.json (git-ignored).  All pipeline layers load their key from here;
no key material is ever accepted from user input.

Usage
-----
    # First run – generate and save keys:
    python -m backend.keys --init

    # In every other module:
    from backend.keys import PLAYFAIR_KEY, COLUMNAR_KEY, DES_KEY
"""

from __future__ import annotations

import argparse
import json
import os
import secrets
import string
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_REPO_ROOT   = Path(__file__).resolve().parent.parent
_KEYS_FILE   = _REPO_ROOT / ".keys.json"       # ← must be in .gitignore
_GITIGNORE   = _REPO_ROOT / ".gitignore"


# ---------------------------------------------------------------------------
# Generation helpers
# ---------------------------------------------------------------------------

def _gen_playfair_key(length: int = 12) -> str:
    """
    Return a random uppercase alphabetic string with no repeated characters,
    drawn from A-Z (I/J merged means 25 usable letters).

    A 12-character key with no repeats gives 25!/(25-12)! ≈ 5.2 × 10¹⁵
    possible squares – far beyond any brute-force attempt.
    """
    alphabet = [c for c in string.ascii_uppercase if c != "J"]  # 25 letters
    sample   = secrets.SystemRandom().sample(alphabet, min(length, 25))
    return "".join(sample)


def _gen_columnar_key(width: int = 9) -> str:
    """
    Return a random permutation of *width* distinct uppercase letters.
    The columnar transposition cipher uses alphabetical rank of each letter
    to determine column read-order, so the key space is width! permutations.

    width=9 → 9! = 362 880 permutations (easily brute-forced on its own,
    but this is Layer 2 of 3 so composite security is the goal).
    Increase to 12 for stronger standalone columnar security.
    """
    alphabet = [c for c in string.ascii_uppercase if c != "J"]
    sample   = secrets.SystemRandom().sample(alphabet, width)
    return "".join(sample)


def _gen_des_key() -> str:
    """
    Return a hex-encoded 8-byte (64-bit) DES key.
    Stored as a 16-character hex string; the DES layer must decode it with
    bytes.fromhex() before use.

    Note: DES has a 56-bit effective key (8 bits are parity) and is
    considered legacy.  It is included here to satisfy the 3-layer
    academic requirement.  For production use, replace with AES-256.
    """
    return secrets.token_hex(8)   # 8 bytes → 16 hex chars


# ---------------------------------------------------------------------------
# Persist / load
# ---------------------------------------------------------------------------

def generate_keys() -> dict[str, str]:
    """Generate a fresh set of keys for all three pipeline layers."""
    return {
        "playfair": _gen_playfair_key(12),
        "columnar":  _gen_columnar_key(9),
        "des":       _gen_des_key(),
    }


def save_keys(keys: dict[str, str], path: Path = _KEYS_FILE) -> None:
    """Write *keys* to *path* with restricted permissions (owner read-only)."""
    path.write_text(json.dumps(keys, indent=2))
    try:
        os.chmod(path, 0o600)   # rw------- (ignored on Windows)
    except NotImplementedError:
        pass

    # Ensure .keys.json is in .gitignore
    _ensure_gitignored(path.name)
    print(f"[keys] Keys written to {path}  (permissions: 600)")


def load_keys(path: Path = _KEYS_FILE) -> dict[str, str]:
    """
    Load keys from *path*.  Raises FileNotFoundError with a helpful message
    if the file does not exist yet (caller should run --init first).
    """
    if not path.exists():
        raise FileNotFoundError(
            f"Key file not found: {path}\n"
            "Run  `python -m backend.keys --init`  to generate system keys."
        )
    data = json.loads(path.read_text())
    _validate_keys(data)
    return data


def _validate_keys(data: dict) -> None:
    """Raise ValueError if any expected key is missing or malformed."""
    required = {
        "playfair": lambda v: isinstance(v, str) and v.isalpha() and len(v) >= 6,
        "columnar":  lambda v: isinstance(v, str) and v.isalpha() and len(v) >= 5,
        "des":       lambda v: isinstance(v, str) and len(v) == 16
                               and all(c in "0123456789abcdef" for c in v),
    }
    for field, check in required.items():
        if field not in data:
            raise ValueError(f"Key file is missing the '{field}' entry.")
        if not check(data[field]):
            raise ValueError(f"Key file has an invalid '{field}' value.")


def _ensure_gitignored(filename: str) -> None:
    """Append *filename* to .gitignore if it is not already listed."""
    if not _GITIGNORE.exists():
        _GITIGNORE.write_text(f"{filename}\n")
        return
    existing = _GITIGNORE.read_text()
    if filename not in existing:
        with _GITIGNORE.open("a") as f:
            f.write(f"\n# Auto-added by keys.py\n{filename}\n")


# ---------------------------------------------------------------------------
# Module-level key constants  (imported by pipeline layers)
# ---------------------------------------------------------------------------

def _load_or_abort() -> dict[str, str]:
    try:
        return load_keys()
    except FileNotFoundError as exc:
        sys.exit(f"[keys] ERROR: {exc}")
    except ValueError as exc:
        sys.exit(f"[keys] ERROR: Corrupt key file – {exc}")


_keys = _load_or_abort() if "--init" not in sys.argv and "--rotate" not in sys.argv else {}

PLAYFAIR_KEY: str = _keys.get("playfair", "")
COLUMNAR_KEY: str  = _keys.get("columnar", "")
DES_KEY_HEX:  str  = _keys.get("des", "")          # hex string; decode before use
DES_KEY:      bytes = bytes.fromhex(_keys.get("des", "0000000000000000")) if _keys.get("des") else b"\x00" * 8


# ---------------------------------------------------------------------------
# CLI  –  python -m backend.keys --init  /  --rotate  /  --show
# ---------------------------------------------------------------------------

def _cli() -> None:
    parser = argparse.ArgumentParser(
        description="Manage system encryption keys for the pipeline."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--init",
        action="store_true",
        help="Generate keys and save to .keys.json (fails if file exists).",
    )
    group.add_argument(
        "--rotate",
        action="store_true",
        help="Overwrite existing keys with freshly generated ones (⚠ all "
             "existing ciphertext becomes permanently unrecoverable).",
    )
    group.add_argument(
        "--show",
        action="store_true",
        help="Print current key metadata (lengths, NOT values) to stdout.",
    )
    args = parser.parse_args()

    if args.init:
        if _KEYS_FILE.exists():
            sys.exit(
                f"[keys] Key file already exists at {_KEYS_FILE}.\n"
                "Use --rotate only if you accept that existing ciphertext "
                "will become unreadable."
            )
        keys = generate_keys()
        save_keys(keys)
        print("[keys] ✓ System keys initialised successfully.")

    elif args.rotate:
        confirm = input(
            "⚠  Rotating keys will make ALL existing ciphertext unrecoverable.\n"
            "Type  YES  to confirm: "
        )
        if confirm.strip() != "YES":
            print("[keys] Rotation cancelled.")
            sys.exit(0)
        keys = generate_keys()
        save_keys(keys)
        print("[keys] ✓ Keys rotated.")

    elif args.show:
        if not _KEYS_FILE.exists():
            sys.exit("[keys] No key file found.  Run --init first.")
        keys = load_keys()
        print(f"  Playfair key  : {'*' * len(keys['playfair'])}  "
              f"(length {len(keys['playfair'])})")
        print(f"  Columnar key  : {'*' * len(keys['columnar'])}   "
              f"(length {len(keys['columnar'])})")
        print(f"  DES key (hex) : {'*' * 16}  (8 bytes / 64-bit)")


if __name__ == "__main__":
    _cli()
