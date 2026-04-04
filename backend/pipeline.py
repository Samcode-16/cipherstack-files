"""
3-Layer Encryption Pipeline

Chains all three ciphers together:
  1. Playfair (substitution cipher - layer 1)
  2. Columnar (transposition cipher - layer 2)
  3. DES (block cipher - layer 3)

Encryption flow:
  plaintext → [Playfair] → [Columnar] → [DES] → hex-encoded ciphertext

Decryption flow:
  hex-encoded ciphertext → [DES] → [Columnar] → [Playfair] → plaintext

The pipeline loads keys from backend.keys module (expects --init to be run first).
"""

from backend import playfair, columnar, des_cipher
from backend.keys import load_keys
from pathlib import Path
import re
import json
import base64


# ---------------------------------------------------------------------------
# Formatting preservation helpers
# ---------------------------------------------------------------------------

def _extract_format_info(plaintext: str) -> dict:
    """
    Extract formatting info from original text.
    Stores: case pattern (upper/lower), position of spaces and punctuation.
    
    Returns dict with 'case_pattern' (binary string) and 'spacing' (list of positions)
    """
    # Store case pattern: 1 for uppercase, 0 for lowercase (letters only)
    case_pattern = ''.join('1' if c.isupper() else '0' for c in plaintext if c.isalpha())
    
    # Store non-alpha characters (spaces, punctuation) with their positions
    spacing_chars = []
    letter_count = 0
    for c in plaintext:
        if c.isalpha():
            letter_count += 1
        elif not c.isalnum():  # Any non-alphanumeric character
            spacing_chars.append({
                'pos': letter_count,  # Position after which this character appears
                'char': c
            })
    
    return {
        'case_pattern': case_pattern,
        'spacing': spacing_chars
    }


def _restore_format(decrypted_text: str, format_info: dict) -> str:
    """
    Restore original formatting (case and spacing) to decrypted text.
    
    Args:
        decrypted_text: The normalized decrypted text (uppercase, no spaces)
        format_info: The formatting metadata extracted during encryption
    
    Returns:
        Text with original formatting restored
    """
    if not format_info:
        return decrypted_text
    
    # Step 1: Restore case
    result = []
    for i, c in enumerate(decrypted_text):
        if i < len(format_info.get('case_pattern', '')):
            if format_info['case_pattern'][i] == '1':
                result.append(c.upper())
            else:
                result.append(c.lower())
        else:
            result.append(c)
    
    text_with_case = ''.join(result)
    
    # Step 2: Restore spacing - insert from right to left
    # For items at same position, insert in reverse order of original appearance
    spacing_list = format_info.get('spacing', [])
    for idx, spacing in sorted(enumerate(spacing_list), key=lambda x: (-x[1]['pos'], -x[0])):
        pos = spacing['pos']
        if pos <= len(text_with_case):
            text_with_case = text_with_case[:pos] + spacing['char'] + text_with_case[pos:]
    
    return text_with_case


# ---------------------------------------------------------------------------
# Pipeline encryption
# ---------------------------------------------------------------------------

def encrypt_text(plaintext: str) -> str:
    """
    Encrypt plaintext through all 3 layers.
    
    Args:
        plaintext: Text to encrypt
    
    Returns:
        Hex-encoded final ciphertext with metadata prefix (can be safely stored/transmitted)
        Format: [4-digit format-len][hex-format-data][4-digit length][2-digit columnar-padding]hex-ciphertext
    
    Raises:
        FileNotFoundError: If keys not initialized (run: python -m backend.keys --init)
        ValueError: If any layer fails
    """
    # Load keys from .keys.json
    keys = load_keys()
    playfair_key = keys["playfair"]
    columnar_key = keys["columnar"]
    des_key = keys["des"]
    
    # STEP 1: Extract and encode formatting info
    format_info = _extract_format_info(plaintext)
    format_json = json.dumps(format_info)
    format_encoded = base64.b64encode(format_json.encode()).hex()  # hex string
    format_len_hex = f"{len(format_encoded)//2:04x}"  # length in hex (in bytes)
    
    # Store original plaintext length (normalized: uppercase, no spaces/punctuation)
    # Store original plaintext length (normalized: uppercase, no spaces/punctuation)
    normalized_plaintext = re.sub(r"[^A-Za-z]", "", plaintext).upper()
    original_length = len(normalized_plaintext)

# For binary-encoded content, store the full string length instead
# so remove_fillers doesn't chop the base64 data
    if plaintext.startswith("BINARY:"):
        original_length = len(normalized_plaintext)
    # We'll use a marker to signal full-string recovery on decrypt
    _full_original_length = len(plaintext)
    
    # Layer 1: Playfair substitution
    layer1 = playfair.encrypt(plaintext, playfair_key)
    
    # Store how much padding Columnar will add
    col_padding_needed = (len(columnar_key) - (len(layer1) % len(columnar_key))) % len(columnar_key)
    
    # Layer 2: Columnar transposition (input from layer1 is uppercase letters)
    layer2 = columnar.encrypt(layer1, columnar_key)
    
    # Layer 3: DES block cipher (convert text to bytes, encrypt, return hex)
    layer3 = des_cipher.encrypt(layer2, des_key)
    
    # Encode metadata into result:
    # [4 hex digits for format length][hex-format-data][4 hex digits for original length][2 hex digits for columnar padding][DES ciphertext]
    result = format_len_hex + format_encoded + f"{original_length:04x}{col_padding_needed:02x}" + layer3
    
    return result


def decrypt_text(ciphertext_hex: str) -> str:
    """
    Decrypt ciphertext through all 3 layers in reverse.
    
    Args:
        ciphertext_hex: Hex-encoded ciphertext from encrypt_text()
                        Format: [4-digit format-len][hex-format-data][4-digit length][2-digit columnar-padding]hex-ciphertext
    
    Returns:
        Decrypted plaintext with original formatting (case and spacing) restored
    
    Raises:
        FileNotFoundError: If keys not initialized
        ValueError: If any layer fails or ciphertext is invalid
    """
    # Load keys from .keys.json
    keys = load_keys()
    playfair_key = keys["playfair"]
    columnar_key = keys["columnar"]
    des_key = keys["des"]
    
    # STEP 1: Extract format info from beginning of ciphertext
    format_info = None
    try:
        format_len = int(ciphertext_hex[:4], 16)  # First 4 hex digits = length in bytes
        format_hex_start = 4
        format_hex_end = format_hex_start + (format_len * 2)  # Each byte = 2 hex chars
        
        if format_hex_end > len(ciphertext_hex):
            # Fallback: old format without formatting info
            format_info = None
            remaining_hex = ciphertext_hex
        else:
            format_hex = ciphertext_hex[format_hex_start:format_hex_end]
            format_encoded = bytes.fromhex(format_hex).decode()
            format_info = json.loads(base64.b64decode(format_encoded).decode())
            remaining_hex = ciphertext_hex[format_hex_end:]
    except Exception:
        # Fallback: couldn't parse format info, try old format
        format_info = None
        remaining_hex = ciphertext_hex
    
    # STEP 2: Extract encryption metadata and decrypt
    try:
        original_length = int(remaining_hex[:4], 16)       # First 4 hex digits
        col_padding_needed = int(remaining_hex[4:6], 16)   # Next 2 hex digits
        des_input_hex = remaining_hex[6:]                  # Rest is DES ciphertext
    except (ValueError, IndexError):
        raise ValueError("Invalid ciphertext format: expected 6+ hex digits for metadata")
    
    # Layer 3: DES block cipher (reverse - decrypt hex to text)
    layer3 = des_cipher.decrypt(des_input_hex, des_key)
    
    # Layer 2: Columnar transposition (reverse)
    layer2 = columnar.decrypt(layer3, columnar_key)
    
    # Remove Columnar padding (the padding we added during encryption)
    if col_padding_needed > 0:
        layer2_unpadded = layer2[:-col_padding_needed]
    else:
        layer2_unpadded = layer2
    
    # Layer 1: Playfair substitution (reverse)
    layer1 = playfair.decrypt(layer2_unpadded, playfair_key)
    
    # Remove Playfair fillers and padding by truncating to original length
    plaintext = playfair.remove_fillers(layer1, original_length)
    
    # STEP 3: Restore original formatting (case and spacing)
    plaintext = _restore_format(plaintext, format_info)
    
    return plaintext


# ---------------------------------------------------------------------------
# Pipeline with file I/O
# ---------------------------------------------------------------------------

def encrypt_file(input_path: str, output_path: str) -> dict:
    """
    Read file, encrypt contents, write to output file.
    
    Args:
        input_path:  Path to plaintext file
        output_path: Path to save encrypted file (will be appended with .encrypted)
    
    Returns:
        Dictionary with encryption stats:
        {
            "status": "success" | "error",
            "input_file": str,
            "output_file": str,
            "original_size": int (bytes),
            "encrypted_size": int (bytes),
            "message": str
        }
    """
    try:
        input_file = Path(input_path)
        if not input_file.exists():
            return {
                "status": "error",
                "input_file": input_path,
                "output_file": None,
                "original_size": 0,
                "encrypted_size": 0,
                "message": f"Input file not found: {input_path}"
            }
        
        # Read plaintext file
        plaintext = input_file.read_text(encoding='utf-8')
        original_size = len(plaintext.encode('utf-8'))
        
        # Encrypt
        ciphertext_hex = encrypt_text(plaintext)
        
        # Write encrypted file
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(ciphertext_hex, encoding='utf-8')
        encrypted_size = len(ciphertext_hex.encode('utf-8'))
        
        return {
            "status": "success",
            "input_file": str(input_file),
            "output_file": str(output_file),
            "original_size": original_size,
            "encrypted_size": encrypted_size,
            "message": f"Encrypted: {original_size} bytes → {encrypted_size} bytes"
        }
    
    except Exception as e:
        return {
            "status": "error",
            "input_file": input_path,
            "output_file": output_path,
            "original_size": 0,
            "encrypted_size": 0,
            "message": f"Encryption failed: {str(e)}"
        }


def decrypt_file(input_path: str, output_path: str) -> dict:
    """
    Read encrypted file, decrypt contents, write to output file.
    
    Args:
        input_path:  Path to encrypted file (hex-encoded)
        output_path: Path to save decrypted file
    
    Returns:
        Dictionary with decryption stats (same structure as encrypt_file)
    """
    try:
        input_file = Path(input_path)
        if not input_file.exists():
            return {
                "status": "error",
                "input_file": input_path,
                "output_file": None,
                "original_size": 0,
                "encrypted_size": 0,
                "message": f"Input file not found: {input_path}"
            }
        
        # Read encrypted file (hex string)
        ciphertext_hex = input_file.read_text(encoding='utf-8')
        encrypted_size = len(ciphertext_hex.encode('utf-8'))
        
        # Decrypt
        plaintext = decrypt_text(ciphertext_hex)
        
        # Write decrypted file
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(plaintext, encoding='utf-8')
        original_size = len(plaintext.encode('utf-8'))
        
        return {
            "status": "success",
            "input_file": str(input_file),
            "output_file": str(output_file),
            "original_size": original_size,
            "encrypted_size": encrypted_size,
            "message": f"Decrypted: {encrypted_size} bytes → {original_size} bytes"
        }
    
    except Exception as e:
        return {
            "status": "error",
            "input_file": input_path,
            "output_file": output_path,
            "original_size": 0,
            "encrypted_size": 0,
            "message": f"Decryption failed: {str(e)}"
        }


# ---------------------------------------------------------------------------
# Pipeline debugging / info
# ---------------------------------------------------------------------------

def get_pipeline_info() -> str:
    """Return human-readable info about the pipeline and loaded keys."""
    try:
        keys = load_keys()
        return (
            "3-Layer Encryption Pipeline\n"
            "=" * 50 + "\n"
            f"Layer 1 - Playfair (Substitution)\n"
            f"  Key: {keys['playfair']}\n"
            f"  Algorithm: 5×5 digraph substitution (I/J merged)\n"
            f"\n"
            f"Layer 2 - Columnar (Transposition)\n"
            f"  Key: {keys['columnar']}\n"
            f"  Algorithm: Row-write, column-read rearrangement\n"
            f"\n"
            f"Layer 3 - DES (Block Cipher)\n"
            f"  Key: {keys['des']}\n"
            f"  Algorithm: DES ECB mode (8-byte blocks, PKCS7 padding)\n"
            f"\nFlow: plaintext → Playfair → Columnar → DES → hex output"
        )
    except FileNotFoundError as e:
        return f"Error: {e}"


# ---------------------------------------------------------------------------
# Quick smoke-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print(get_pipeline_info())
    print("\n" + "=" * 50 + "\n")
    
    # Test text encryption
    test_text = "HELLO WORLD"
    try:
        encrypted = encrypt_text(test_text)
        print(f"Original:  {test_text}")
        print(f"Encrypted: {encrypted[:60]}...")
        
        decrypted = decrypt_text(encrypted)
        print(f"Decrypted: {decrypted}")
    except FileNotFoundError as e:
        print(f"Error: {e}")
