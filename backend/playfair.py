"""
Playfair Cipher - Layer 1 of the encryption pipeline.

Key:    A string used to build a 5x5 Polybius square (I/J merged).
Rules:
  - Same-row pair    → shift right  (wrap)
  - Same-col pair    → shift down   (wrap)
  - Rectangle pair   → swap columns
  - Digraph padding  → 'X' inserted between duplicate letters
  - Odd-length input → 'X' appended
"""

import re
import string


# ---------------------------------------------------------------------------
# Key-square construction
# ---------------------------------------------------------------------------

def _build_square(key: str) -> list[list[str]]:
    """Return a 5×5 Playfair square derived from *key*."""
    key = key.upper().replace("J", "I")
    seen: set[str] = set()
    order: list[str] = []

    for ch in key + string.ascii_uppercase:
        if ch == "J":
            continue
        if ch not in seen and ch in string.ascii_uppercase:
            seen.add(ch)
            order.append(ch)

    return [order[i * 5:(i + 1) * 5] for i in range(5)]


def _square_index(square: list[list[str]], ch: str) -> tuple[int, int]:
    """Return (row, col) of *ch* in *square*."""
    for r, row in enumerate(square):
        if ch in row:
            return r, row.index(ch)
    raise ValueError(f"Character '{ch}' not found in Playfair square.")


# ---------------------------------------------------------------------------
# Digraph preparation
# ---------------------------------------------------------------------------

def _prepare_plaintext(text: str) -> list[tuple[str, str]]:
    """
    Clean *text*, insert filler 'X' between duplicate letters in a digraph,
    pad to even length, and return a list of (a, b) digraph tuples.
    
    Uses 'X' as filler - works better for English text which rarely has X.
    """
    text = re.sub(r"[^A-Za-z]", "", text).upper().replace("J", "I")
    digraphs: list[tuple[str, str]] = []
    i = 0

    while i < len(text):
        a = text[i]
        if i + 1 >= len(text):
            # Odd length – pad with X
            b = "X" if a != "X" else "Z"
            digraphs.append((a, b))
            i += 1
        elif text[i + 1] == a:
            # Duplicate pair – insert filler X
            # This marks a duplicate that will need special handling on decrypt
            b = "X"
            digraphs.append((a, b))
            i += 1          # do NOT advance past text[i+1]; it starts next pair
        else:
            digraphs.append((a, text[i + 1]))
            i += 2

    return digraphs


# ---------------------------------------------------------------------------
# Core encrypt / decrypt helpers
# ---------------------------------------------------------------------------

def _process_digraph(
    square: list[list[str]],
    a: str,
    b: str,
    encrypt: bool,
) -> tuple[str, str]:
    """Apply Playfair rules to one digraph; direction controlled by *encrypt*."""
    shift = 1 if encrypt else -1

    ra, ca = _square_index(square, a)
    rb, cb = _square_index(square, b)

    if ra == rb:                                    # Same row
        return square[ra][(ca + shift) % 5], square[rb][(cb + shift) % 5]
    elif ca == cb:                                  # Same column
        return square[(ra + shift) % 5][ca], square[(rb + shift) % 5][cb]
    else:                                           # Rectangle
        return square[ra][cb], square[rb][ca]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def encrypt(plaintext: str, key: str) -> str:
    """
    Encrypt *plaintext* with the Playfair cipher using *key*.

    Returns uppercase ciphertext (letters only, no spaces).
    """
    square = _build_square(key)
    digraphs = _prepare_plaintext(plaintext)
    result: list[str] = []

    for a, b in digraphs:
        ea, eb = _process_digraph(square, a, b, encrypt=True)
        result.extend([ea, eb])

    return "".join(result)


def decrypt(ciphertext: str, key: str) -> str:
    """
    Decrypt *ciphertext* with the Playfair cipher using *key*.

    Returns uppercase plaintext.  Note: filler 'X' characters inserted
    during encryption are *not* removed automatically because the cipher
    is not self-delimiting – the caller or pipeline layer should strip them
    if needed.
    """
    square = _build_square(key)
    ciphertext = re.sub(r"[^A-Za-z]", "", ciphertext).upper().replace("J", "I")

    if len(ciphertext) % 2 != 0:
        raise ValueError("Ciphertext length must be even for Playfair decryption.")

    result: list[str] = []
    for i in range(0, len(ciphertext), 2):
        a, b = ciphertext[i], ciphertext[i + 1]
        da, db = _process_digraph(square, a, b, encrypt=False)
        result.extend([da, db])

    return "".join(result)


def get_square_display(key: str) -> str:
    """Return a human-readable 5×5 grid string for debugging / UI display."""
    square = _build_square(key)
    rows = [" ".join(row) for row in square]
    header = f"Playfair Square  (key='{key.upper()}')\n" + "-" * 11
    return header + "\n" + "\n".join(rows)


def remove_fillers(text: str, original_length: int) -> str:
    """
    Remove Playfair fillers and padding to recover original length.
    
    During encryption, filler X's are inserted between duplicate letters to make them
    into separate digraphs, and trailing X may be added for odd-length text. This function
    removes those fillers by:
    1. Identifying X characters  
    2. Removing them
    3. Truncating to original length
    
    NOTE: This assumes the original plaintext contains few (if any) X characters.
          This is valid for most English text where X appears in < 1% of messages.
    
    Args:
        text: Decrypted Playfair output (may contain filler X's and padding)
        original_length: The original plaintext length before Playfair encryption
    
    Returns:
        Text with X fillers removed if possible, or truncated to original_length
    """
    # Strategy: Remove X characters until we reach the original length
    # This works because Playfair only adds X's, not removes characters
    
    # If text already matches original length, return as-is
    if len(text) == original_length:
        return text
    
    # If text is longer, remove X's to bring it down to original length
    if len(text) > original_length:
        # Count how many excess characters we have
        excess = len(text) - original_length
        
        # Try to remove X's first (they're likely fillers)
        x_count = text.count('X')
        x_to_remove = min(excess, x_count)
        
        if x_to_remove > 0:
            # Remove X's from the text
            result = text
            for _ in range(x_to_remove):
                result = result.replace('X', '', 1)  # Remove one X at a time
            
            # If we've removed enough, return
            if len(result) == original_length:
                return result
            
            # If not, truncate the rest
            return result[:original_length]
        else:
            # No X's to remove, just truncate
            return text[:original_length]
    
    # If text is shorter than original length, return as-is
    # (This shouldn't happen if encryption/decryption is correct)
    return text


# ---------------------------------------------------------------------------
# Quick smoke-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    KEY = "MONARCHY"
    MESSAGE = "INSTRUMENTS"

    print(get_square_display(KEY))
    print()

    ct = encrypt(MESSAGE, KEY)
    print(f"Plaintext : {MESSAGE}")
    print(f"Encrypted : {ct}")

    dt = decrypt(ct, KEY)
    print(f"Decrypted : {dt}")
