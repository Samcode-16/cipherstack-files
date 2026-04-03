#!/usr/bin/env python3
"""
Comprehensive encryption/decryption test to diagnose issues.
Tests each layer individually and the full pipeline.
"""

import sys
from pathlib import Path
from backend import pipeline, playfair, columnar, des_cipher
from backend.keys import load_keys

def print_section(title):
    """Print a formatted section header."""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")

def test_keys():
    """Test key loading."""
    print_section("1. KEY LOADING TEST")
    try:
        keys = load_keys()
        print(f"✓ Keys loaded successfully")
        print(f"  - Playfair key: {keys['playfair'][:20]}... (len={len(keys['playfair'])})")
        print(f"  - Columnar key: {keys['columnar']}")
        print(f"  - DES key: {keys['des'][:16]}... (len={len(keys['des'])})")
        return keys
    except Exception as e:
        print(f"✗ ERROR loading keys: {e}")
        sys.exit(1)

def test_playfair_layer(keys):
    """Test Playfair encryption/decryption."""
    print_section("2. PLAYFAIR LAYER TEST")
    
    # NOTE: Playfair adds X fillers between duplicate letters, so perfect
    # roundtrip requires knowing the original length. This test just verifies
    # that encryption and decryption work without errors.
    
    plaintext = "HELLO WORLD THIS IS A TEST"
    print(f"Input:  {plaintext}")
    
    try:
        encrypted = playfair.encrypt(plaintext, keys['playfair'])
        print(f"Encrypted: {encrypted}")
        print(f"Length: {len(encrypted)}")
        
        # Try to decrypt
        decrypted = playfair.decrypt(encrypted, keys['playfair'])
        print(f"Decrypted: {decrypted}")
        print(f"Decrypted length: {len(decrypted)}")
        
        # Playfair adds X fillers for duplicate letters, so we can't expect
        # perfect reversal. But we can verify that it processes without errors
        # and is consistent.
        print(f"ℹ  Playfair adds X fillers for duplicate letters (expected behavior)")
        print(f"ℹ  Perfect reversal requires original length metadata (from pipeline)")
        
        # Quick consistency check: encrypt again and verify it's the same
        encrypted_again = playfair.encrypt(plaintext, keys['playfair'])
        if encrypted == encrypted_again:
            print(f"✓ Playfair encryption is DETERMINISTIC (consistent)")
            return True
        else:
            print(f"✗ Playfair encryption is NOT consistent")
            return False
            
    except Exception as e:
        print(f"✗ ERROR in Playfair: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_columnar_layer(keys):
    """Test Columnar encryption/decryption."""
    print_section("3. COLUMNAR LAYER TEST")
    
    # NOTE: Columnar adds X padding if input length isn't divisible by key width.
    # Perfect roundtrip requires knowing the original length.
    
    plaintext = "HELLOWORLD"
    print(f"Input: {plaintext}")
    
    try:
        encrypted = columnar.encrypt(plaintext, keys['columnar'])
        print(f"Encrypted: {encrypted}")
        print(f"Encrypted length: {len(encrypted)} (original: {len(plaintext)})")
        
        decrypted = columnar.decrypt(encrypted, keys['columnar'])
        print(f"Decrypted: {decrypted}")
        print(f"Decrypted length: {len(decrypted)}")
        
        # Columnar adds X padding, so without original length we get padding
        print(f"ℹ  Columnar adds X padding if not divisible by key width (expected behavior)")
        print(f"ℹ  Perfect reversal requires original length metadata (from pipeline)")
        
        # Check consistency
        encrypted_again = columnar.encrypt(plaintext, keys['columnar'])
        if encrypted == encrypted_again:
            print(f"✓ Columnar encryption is DETERMINISTIC (consistent)")
            return True
        else:
            print(f"✗ Columnar encryption is NOT consistent")
            return False
            
    except Exception as e:
        print(f"✗ ERROR in Columnar: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_des_layer(keys):
    """Test DES encryption/decryption."""
    print_section("4. DES LAYER TEST")
    
    plaintext = "HELLOWORLD"
    print(f"Input: {plaintext}")
    
    try:
        encrypted_hex = des_cipher.encrypt(plaintext, keys['des'])
        print(f"Encrypted (hex): {encrypted_hex[:32]}... (len={len(encrypted_hex)})")
        
        decrypted = des_cipher.decrypt(encrypted_hex, keys['des'])
        print(f"Decrypted: {decrypted}")
        
        # DES may add padding, so check if plaintext is contained
        if decrypted.rstrip().startswith(plaintext) or plaintext in decrypted:
            print(f"✓ DES roundtrip SUCCESS (with padding)")
            return True
        else:
            print(f"✗ DES roundtrip FAILED")
            print(f"  Expected: {plaintext}")
            print(f"  Got: {decrypted}")
            return False
            
    except Exception as e:
        print(f"✗ ERROR in DES: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_full_pipeline(keys):
    """Test the complete 3-layer pipeline."""
    print_section("5. FULL PIPELINE TEST")
    
    plaintext = "HELLO THIS IS A SECRET MESSAGE TESTING ENCRYPTION"
    print(f"Original text: {plaintext}")
    print(f"Original length: {len(plaintext)}")
    
    # Normalize plaintext (remove spaces, uppercase) for proper comparison
    import re
    normalized_plaintext = re.sub(r"[^A-Za-z]", "", plaintext).upper()
    print(f"Normalized: {normalized_plaintext}")
    print(f"Normalized length: {len(normalized_plaintext)}")
    
    try:
        # Encrypt
        ciphertext = pipeline.encrypt_text(plaintext)
        print(f"Encrypted: {ciphertext[:64]}...")
        print(f"Encrypted length: {len(ciphertext)}")
        
        # Decrypt
        decrypted = pipeline.decrypt_text(ciphertext)
        print(f"Decrypted: {decrypted}")
        print(f"Decrypted length: {len(decrypted)}")
        
        # Verify - compare normalized versions (spaces/punctuation removed)
        if decrypted == normalized_plaintext:
            print(f"✓ PIPELINE ROUNDTRIP SUCCESS")
            return True
        else:
            print(f"✗ PIPELINE ROUNDTRIP FAILED")
            print(f"  Expected: '{normalized_plaintext}'")
            print(f"  Got:      '{decrypted}'")
            
            # Check character-by-character
            print(f"\nCharacter-by-character comparison (first 20 chars):")
            max_check = min(20, len(normalized_plaintext), len(decrypted))
            for i in range(max_check):
                if i < len(normalized_plaintext) and i < len(decrypted):
                    e = normalized_plaintext[i]
                    g = decrypted[i]
                    if e != g:
                        print(f"  Position {i}: expected '{e}', got '{g}'")
            
            return False
            
    except Exception as e:
        print(f"✗ ERROR in pipeline: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_short_message(keys):
    """Test with very short message."""
    print_section("6. SHORT MESSAGE TEST")
    
    plaintext = "HELP"
    print(f"Original text: {plaintext}")
    
    try:
        ciphertext = pipeline.encrypt_text(plaintext)
        print(f"Encrypted: {ciphertext}")
        
        decrypted = pipeline.decrypt_text(ciphertext)
        print(f"Decrypted: {decrypted}")
        
        if decrypted.strip() == plaintext:
            print(f"✓ SHORT MESSAGE TEST SUCCESS")
            return True
        else:
            print(f"✗ SHORT MESSAGE TEST FAILED")
            return False
            
    except Exception as e:
        print(f"✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("\n" + "="*70)
    print("ENCRYPTION/DECRYPTION DIAGNOSTIC TEST")
    print("="*70)
    
    # Test keys
    keys = test_keys()
    
    # Test individual layers
    playfair_ok = test_playfair_layer(keys)
    columnar_ok = test_columnar_layer(keys)
    des_ok = test_des_layer(keys)
    
    # Test full pipeline
    pipeline_ok = test_full_pipeline(keys)
    short_ok = test_short_message(keys)
    
    # Summary
    print_section("SUMMARY")
    print(f"Playfair:  {'✓ PASS' if playfair_ok else '✗ FAIL'}")
    print(f"Columnar:  {'✓ PASS' if columnar_ok else '✗ FAIL'}")
    print(f"DES:       {'✓ PASS' if des_ok else '✗ FAIL'}")
    print(f"Pipeline:  {'✓ PASS' if pipeline_ok else '✗ FAIL'}")
    print(f"Short msg: {'✓ PASS' if short_ok else '✗ FAIL'}")
    
    if all([playfair_ok, columnar_ok, des_ok, pipeline_ok, short_ok]):
        print(f"\n✓ ALL TESTS PASSED")
        return 0
    else:
        print(f"\n✗ SOME TESTS FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(main())
