"""
Columnar Transposition Cipher - Layer 2 of the encryption pipeline.

Encrypts text that has  already been processed by Playfair (so all input
is uppercase letters only, with digraph structure).

Key:    A string used to determine the column order.
Rules:
  - Key characters are numbered based on alphabetical order (A=1, B=2, ...)
  - Plaintext is written row by row in a grid with columns = len(key)
  - Ciphertext is read column by column following the key order
  - Padding: If plaintext length is not divisible by key length, 'X' is appended

Alignment with Playfair:
  - Input is always uppercase letters (A-Z), no repeats in key letter order
  - Even-length strings (from Playfair digraphs)
"""

import re
import string


# ---------------------------------------------------------------------------
# Key processing
# ---------------------------------------------------------------------------

def _get_column_order(key: str) -> list[int]:
    """
    Return the column order derived from *key*.
    
    Example: key="KEY" → ['K','E','Y'] → [3, 1, 2] 
             (K=3rd alphabetically, E=1st, Y=2nd)
    """
    key = key.upper().replace("J", "I")  # Align with Playfair convention
    if len(key) == 0:
        raise ValueError("Key cannot be empty")
    
    # Create list of (character, original_position) tuples
    indexed_key = [(ch, idx) for idx, ch in enumerate(key)]
    
    # Sort by character alphabetically
    sorted_key = sorted(indexed_key, key=lambda x: x[0])
    
    # Create order mapping: position → rank
    order = [0] * len(key)
    for rank, (ch, original_pos) in enumerate(sorted_key):
        order[original_pos] = rank
    
    return order


def _pad_plaintext(text: str, key_len: int) -> str:
    """
    Pad plaintext to multiple of key_len using 'X'.
    
    For better alignment with Playfair (which maintains even-length text),
    only pad if necessary to reach minimum grid size. This minimizes
    extra padding that would confuse the decryption process.
    
    Input should be uppercase letters only (from Playfair output).
    Removes any non-alphabetic characters and pads to grid rows if needed.
    """
    text = re.sub(r"[^A-Za-z]", "", text).upper().replace("J", "I")
    remainder = len(text) % key_len
    # Only pad if text length is not already a multiple of key_len
    if remainder != 0:
        text += "X" * (key_len - remainder)
    return text


# ---------------------------------------------------------------------------
# Core encryption / decryption
# ---------------------------------------------------------------------------

def _encrypt_block(plaintext: str, key: str) -> str:
    """
    Encrypt a single block of plaintext using columnar transposition.
    
    Input: Letters only (from Playfair), padded to even length
    Output: Rearranged letters via column transposition
    """
    key_len = len(key)
    column_order = _get_column_order(key)
    
    # Pad plaintext to grid rows
    plaintext = _pad_plaintext(plaintext, key_len)
    
    # Arrange plaintext in rows (width = key_len)
    rows = [plaintext[i:i + key_len] for i in range(0, len(plaintext), key_len)]
    
    # Extract columns
    columns = []
    for col_idx in range(key_len):
        column = "".join(row[col_idx] for row in rows)
        columns.append(column)
    
    # Read columns in order determined by key rank
    ciphertext = ""
    for rank in range(key_len):
        # Find which column has this rank
        for col_idx, col_rank in enumerate(column_order):
            if col_rank == rank:
                ciphertext += columns[col_idx]
                break
    
    return ciphertext


def _decrypt_block(ciphertext: str, key: str) -> str:
    """
    Decrypt a single block of ciphertext using columnar transposition.
    
    Reverses the column reordering to retrieve the original plaintext.
    """
    key_len = len(key)
    column_order = _get_column_order(key)
    
    # Clean ciphertext (letters only, matching Playfair output)
    ciphertext = re.sub(r"[^A-Za-z]", "", ciphertext).upper().replace("J", "I")
    
    if len(ciphertext) % key_len != 0:
        raise ValueError("Ciphertext length must be divisible by key length")
    
    # Calculate column height
    col_height = len(ciphertext) // key_len
    
    # Reconstruct columns from ciphertext (which is read in rank order)
    columns = [None] * key_len
    pos = 0
    for rank in range(key_len):
        # Find which column has this rank
        for col_idx, col_rank in enumerate(column_order):
            if col_rank == rank:
                columns[col_idx] = ciphertext[pos:pos + col_height]
                pos += col_height
                break
    
    # Arrange columns back into grid
    plaintext = ""
    for row_idx in range(col_height):
        for col_idx in range(key_len):
            plaintext += columns[col_idx][row_idx]
    
    return plaintext


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def encrypt(plaintext: str, key: str) -> str:
    """
    Encrypt *plaintext* with the Columnar Transposition cipher using *key*.
    
    Returns uppercase ciphertext (alphanumeric only, no spaces).
    For longer texts, can be called multiple times or internally chunked.
    """
    if len(plaintext) == 0:
        return ""
    
    return _encrypt_block(plaintext, key)


def decrypt(ciphertext: str, key: str) -> str:
    """
    Decrypt *ciphertext* with the Columnar Transposition cipher using *key*.
    
    Returns uppercase plaintext (with padding characters like 'X' still present).
    The caller should strip padding if needed.
    """
    if len(ciphertext) == 0:
        return ""
    
    return _decrypt_block(ciphertext, key)


def get_key_order_display(key: str) -> str:
    """Return a human-readable display of how the key maps to column order."""
    key = key.upper()
    column_order = _get_column_order(key)
    
    # Create display
    header = f"Columnar Cipher Key Analysis  (key='{key}')\n" + "-" * 40
    
    # Show each character with its rank
    lines = [header]
    lines.append("Position | Character | Rank (Read Order)")
    lines.append("-" * 38)
    for pos, ch in enumerate(key):
        rank = column_order[pos]
        lines.append(f"   {pos}    |     {ch}     |      {rank}")
    
    lines.append("\nColumn read order: " + " → ".join(str(column_order[i]) for i in sorted(range(len(key)), key=lambda i: column_order[i])))
    
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Quick smoke-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    KEY = "SECRET"
    MESSAGE = "HELLOWORLD"
    
    print(get_key_order_display(KEY))
    print("\n" + "=" * 50 + "\n")
    
    ct = encrypt(MESSAGE, KEY)
    print(f"Plaintext : {MESSAGE}")
    print(f"Encrypted : {ct}")
    
    dt = decrypt(ct, KEY)
    print(f"Decrypted : {dt}")
    print(f"\n(Note: Padding 'X' is preserved; caller should remove if needed)")
