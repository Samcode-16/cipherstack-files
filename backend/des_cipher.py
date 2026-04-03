"""
DES Cipher - Layer 3 of the encryption pipeline.

Key:    A 64-bit (8-byte) DES key provided as a hex string (16 chars).
Mode:   ECB (Electronic Codebook) for academic purposes.

Note: DES is considered legacy (56-bit effective key). This implementation
uses the Crypto.Cipher.DES from pycryptodome for compatibility and standard
compliance. For production, use AES-256 instead.

Alignment:
  - Input: Any bytes (output from columnar text or raw binary)
  - Output: Hex-encoded binary (for text transport and file storage)
"""

from Crypto.Cipher import DES
from Crypto.Random import get_random_bytes
import binascii


# ---------------------------------------------------------------------------
# Key validation
# ---------------------------------------------------------------------------

def _validate_des_key(key_hex: str) -> bytes:
    """
    Validate and convert hex string key to 8-byte DES key.
    
    Args:
        key_hex: 16-character hex string (e.g., "0123456789abcdef")
    
    Returns:
        8-byte key suitable for DES
    
    Raises:
        ValueError: If key is invalid format or wrong length
    """
    if not isinstance(key_hex, str):
        raise ValueError("DES key must be a hex string")
    
    if len(key_hex) != 16:
        raise ValueError(f"DES key must be 16 hex chars (8 bytes), got {len(key_hex)}")
    
    try:
        key_bytes = bytes.fromhex(key_hex)
    except ValueError:
        raise ValueError(f"DES key must be valid hex (0-9a-f), got '{key_hex}'")
    
    return key_bytes


def _pad_plaintext_des(plaintext_bytes: bytes) -> bytes:
    """
    Apply PKCS7 padding to plaintext.
    
    DES requires blocks of exactly 8 bytes. PKCS7 pads with bytes
    equal to the number of bytes added (e.g., 4 bytes of padding = 0x04).
    
    Args:
        plaintext_bytes: Input bytes (any length)
    
    Returns:
        Padded bytes (length % 8 == 0)
    """
    block_size = DES.block_size  # 8 bytes
    pad_len = block_size - (len(plaintext_bytes) % block_size)
    padding = bytes([pad_len] * pad_len)
    return plaintext_bytes + padding


def _unpad_plaintext_des(plaintext_bytes: bytes) -> bytes:
    """
    Remove PKCS7 padding from plaintext.
    
    Args:
        plaintext_bytes: Padded plaintext bytes
    
    Returns:
        Unpadded plaintext bytes
    
    Raises:
        ValueError: If padding is invalid
    """
    pad_len = plaintext_bytes[-1]
    if pad_len > DES.block_size or pad_len == 0:
        raise ValueError("Invalid PKCS7 padding")
    
    # Verify all padding bytes are correct
    if plaintext_bytes[-pad_len:] != bytes([pad_len] * pad_len):
        raise ValueError("Invalid PKCS7 padding")
    
    return plaintext_bytes[:-pad_len]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def encrypt(plaintext: str, key_hex: str) -> str:
    """
    Encrypt plaintext using DES in ECB mode.
    
    Args:
        plaintext: Text to encrypt (will be encoded as UTF-8)
        key_hex:   DES key as hex string (16 chars, 8 bytes)
    
    Returns:
        Ciphertext as hex string (can be safely transmitted/stored)
    
    Raises:
        ValueError: If key or plaintext is invalid
    """
    # Validate and prepare key
    key_bytes = _validate_des_key(key_hex)
    
    # Convert plaintext to bytes
    plaintext_bytes = plaintext.encode('utf-8')
    
    # Apply PKCS7 padding
    padded = _pad_plaintext_des(plaintext_bytes)
    
    # Create cipher and encrypt
    cipher = DES.new(key_bytes, DES.MODE_ECB)
    ciphertext_bytes = cipher.encrypt(padded)
    
    # Return as hex string for safe transport
    return binascii.hexlify(ciphertext_bytes).decode('ascii')


def decrypt(ciphertext_hex: str, key_hex: str) -> str:
    """
    Decrypt DES ciphertext.
    
    Args:
        ciphertext_hex: Hex-encoded ciphertext
        key_hex:        DES key as hex string (16 chars, 8 bytes)
    
    Returns:
        Decrypted plaintext (UTF-8 text)
    
    Raises:
        ValueError: If key or ciphertext is invalid
    """
    # Validate and prepare key
    key_bytes = _validate_des_key(key_hex)
    
    # Convert hex ciphertext to bytes
    try:
        ciphertext_bytes = binascii.unhexlify(ciphertext_hex)
    except (binascii.Error, ValueError):
        raise ValueError("Ciphertext must be valid hex string")
    
    if len(ciphertext_bytes) % DES.block_size != 0:
        raise ValueError("Ciphertext length must be multiple of 8 bytes")
    
    # Create cipher and decrypt
    cipher = DES.new(key_bytes, DES.MODE_ECB)
    padded_plaintext = cipher.decrypt(ciphertext_bytes)
    
    # Remove PKCS7 padding
    plaintext_bytes = _unpad_plaintext_des(padded_plaintext)
    
    # Decode to UTF-8 string
    return plaintext_bytes.decode('utf-8')


def get_key_info(key_hex: str) -> str:
    """Return debug info about the DES key."""
    try:
        key_bytes = _validate_des_key(key_hex)
        return (
            f"DES Key Info:\n"
            f"  Hex:      {key_hex}\n"
            f"  Bytes:    {key_bytes.hex()}\n"
            f"  Length:   {len(key_bytes)} bytes (64 bits DES, 56 bits effective)\n"
            f"  Mode:     ECB (Electronic Codebook)\n"
            f"  Block:    8 bytes"
        )
    except ValueError as e:
        return f"Invalid DES key: {e}"


# ---------------------------------------------------------------------------
# Quick smoke-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    KEY_HEX = "0123456789abcdef"
    MESSAGE = "HELLOWORLD"
    
    print(get_key_info(KEY_HEX))
    print()
    
    ct = encrypt(MESSAGE, KEY_HEX)
    print(f"Plaintext : {MESSAGE}")
    print(f"Encrypted : {ct}")
    
    dt = decrypt(ct, KEY_HEX)
    print(f"Decrypted : {dt}")
