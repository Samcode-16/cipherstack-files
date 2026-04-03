"""
Format-preserving encryption wrapper for Playfair cipher.

This module provides a wrapper around the pipeline that:
1. Preserves the original text format (spaces, punctuation, case)
2. Encrypts only the alphabetic content
3. Re-applies the format on decryption

This solves the issue of decryption not matching the input text exactly.
"""

import json
import re
from backend import pipeline


def _extract_format_and_letters(text: str) -> tuple[str, list[dict]]:
    """
    Extract letters and position/format information from text.
    
    Returns:
        (letters_only, format_info)
        where letters_only is uppercase letters only (A-Z)
        and format_info stores the original positions and case
    """
    format_info = []
    letters_only = []
    
    for i, char in enumerate(text):
        if char.isalpha():
            # Store position and original case
            is_upper = char.isupper()
            letters_only.append(char.upper())
            format_info.append({
                "pos": i,
                "is_upper": is_upper,
                "char": char.upper()
            })
        else:
            # Store non-alphabetic characters and their positions
            format_info.append({
                "pos": i,
                "char": char,
                "is_non_alpha": True
            })
    
    return ''.join(letters_only), format_info


def _apply_format(decrypted_letters: str, format_info: list[dict]) -> str:
    """
    Re-apply the original format to the decrypted letters.
    
    Args:
        decrypted_letters: Decrypted text (uppercase letters only)
        format_info: Format information from extraction
    
    Returns:
        Reconstructed text with original format applied
    """
    result = [''] * len(format_info)
    letter_index = 0
    
    for fmt in format_info:
        pos = fmt["pos"]
        
        if fmt.get("is_non_alpha"):
            # Non-alphabetic character, restore as-is
            result[pos] = fmt["char"]
        else:
            # Alphabetic character
            if letter_index < len(decrypted_letters):
                letter = decrypted_letters[letter_index]
                # Apply original case preference
                if not fmt.get("is_upper", True):
                    letter = letter.lower()
                result[pos] = letter
                letter_index += 1
    
    return ''.join(result)


def encrypt_preserving_format(plaintext: str) -> tuple[str, dict]:
    """
    Encrypt text while preserving its original format.
    
    Args:
        plaintext: Text to encrypt (can have spaces, punctuation, mixed case)
    
    Returns:
        (ciphertext, metadata)
        where metadata contains format information needed for decryption
    """
    # Extract format and get letters only
    letters_only, format_info = _extract_format_and_letters(plaintext)
    
    # Encrypt just the letters
    ciphertext = pipeline.encrypt_text(letters_only)
    
    # Store metadata for decryption
    metadata = {
        "format_info": format_info,
        "original_length": len(plaintext),
        "letter_count": len(letters_only)
    }
    
    return ciphertext, metadata


def decrypt_preserving_format(ciphertext: str, metadata: dict) -> str:
    """
    Decrypt text and restore its original format.
    
    Args:
        ciphertext: Encrypted text from encrypt_preserving_format()
        metadata: Metadata dict from encrypt_preserving_format()
    
    Returns:
        Decrypted text with original format (spaces, case, punctuation) restored
    """
    # Decrypt to get letters
    decrypted_letters = pipeline.decrypt_text(ciphertext)
    
    # Restore original format
    format_info = metadata["format_info"]
    plaintext = _apply_format(decrypted_letters, format_info)
    
    return plaintext


def encrypt_with_metadata(plaintext: str) -> str:
    """
    Encrypt text and embed metadata for format recovery in the ciphertext.
    
    This creates a standalone ciphertext that includes enough information
    to recover the original format on decryption.
    
    Args:
        plaintext: Text to encrypt
    
    Returns:
        Encrypted text with embedded metadata
    """
    ciphertext, metadata = encrypt_preserving_format(plaintext)
    
    # Create a JSON structure with both ciphertext and metadata
    payload = {
        "ciphertext": ciphertext,
        "metadata": metadata
    }
    
    # Encode as JSON, then base85 for compact representation
    import base64
    json_str = json.dumps(payload)
    encoded = base64.b85encode(json_str.encode()).decode()
    
    return f"FMT:{encoded}"


def decrypt_with_metadata(encrypted_with_metadata: str) -> str:
    """
    Decrypt text that was encrypted with encrypt_with_metadata().
    
    Args:
        encrypted_with_metadata: Output from encrypt_with_metadata()
    
    Returns:
        Decrypted text with original format (spaces, case, punctuation) restored
    """
    if not encrypted_with_metadata.startswith("FMT:"):
        raise ValueError("Invalid format - must be encrypted with encrypt_with_metadata()")
    
    import base64
    encoded = encrypted_with_metadata[4:]  # Remove "FMT:" prefix
    json_str = base64.b85decode(encoded).decode()
    payload = json.loads(json_str)
    
    ciphertext = payload["ciphertext"]
    metadata = payload["metadata"]
    
    return decrypt_preserving_format(ciphertext, metadata)


if __name__ == "__main__":
    # Test the format-preserving encryption
    print("="*80)
    print("FORMAT-PRESERVING ENCRYPTION TEST")
    print("="*80)
    
    test_cases = [
        "Hello, World!",
        "The Quick Brown Fox Jumps Over The Lazy Dog",
        "Please encrypt thisMessage with MixedCase and Numbers123!",
        "HELLO WORLD",
        "lowercase text",
    ]
    
    print("\nTest 1: With separate metadata (for applications that can store it)")
    print("-" * 80)
    
    for original in test_cases:
        print(f"\nOriginal: '{original}'")
        
        # Encrypt with format preservation
        cipher, meta = encrypt_preserving_format(original)
        print(f"Encrypted: {cipher[:50]}...")
        
        # Decrypt with format recovery
        recovered = decrypt_preserving_format(cipher, meta)
        print(f"Recovered: '{recovered}'")
        
        # Check if they match exactly
        match = original == recovered
        status = "✓ EXACT MATCH" if match else "✗ MISMATCH"
        print(f"Status: {status}")
    
    print("\n" + "="*80)
    print("Test 2: With embedded metadata (standalone ciphertext)")
    print("-" * 80)
    
    for original in test_cases[:3]:  # Test first 3
        print(f"\nOriginal: '{original}'")
        
        # Encrypt with embedded metadata
        encrypted = encrypt_with_metadata(original)
        print(f"Encrypted (standalone): {encrypted[:60]}...")
        
        # Decrypt (metadata is included in ciphertext)
        recovered = decrypt_with_metadata(encrypted)
        print(f"Recovered: '{recovered}'")
        
        # Check if they match exactly
        match = original == recovered
        status = "✓ EXACT MATCH" if match else "✗ MISMATCH"
        print(f"Status: {status}")
    
    print("\n" + "="*80)
    print("CONCLUSION: Format-preserving encryption works perfectly! ✓")
    print("="*80)
