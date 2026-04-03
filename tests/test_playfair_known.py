#!/usr/bin/env python3
"""
Test Playfair with known cipher text examples.
"""

from backend import playfair

def test_known_examples():
    """Test with known Playfair cipher examples."""
    print("="*80)
    print("PLAYFAIR CIPHER - KNOWN EXAMPLES TEST")
    print("="*80)
    
    # Classic Playfair example
    test_cases = [
        {
            "key": "MONARCHY",
            "plaintext": "INSTRUMENTS",
            "expected_ciphertext": "GIQWVUJVDSA"
        },
        {
            "key": "MONARCHY",
            "plaintext": "HELLO",
            "expected_ciphertext": "VGIHXW"  # Let me check this
        }
    ]
    
    for tc in test_cases:
        key = tc["key"]
        plaintext = tc["plaintext"]
        expected_cipher = tc.get("expected_ciphertext", "UNKNOWN")
        
        print(f"\nKey: {key}")
        print(f"Plaintext: {plaintext}")
        print(f"Expected ciphertext: {expected_cipher}")
        
        try:
            # Encrypt
            encrypted = playfair.encrypt(plaintext, key)
            print(f"Actual encrypted: {encrypted}")
            
            # Try to decrypt
            decrypted = playfair.decrypt(encrypted, key)
            print(f"Decrypted: {decrypted}")
            
            # Check if roundtrip works
            if decrypted.rstrip('X') == plaintext.replace('J', 'I'):
                print(f"✓ Roundtrip successful (after removing padding X)")
            else:
                print(f"✗ Roundtrip failed")
                print(f"  Expected: {plaintext}")
                print(f"  Got: {decrypted}")
        
        except Exception as e:
            print(f"✗ ERROR: {e}")
            import traceback
            traceback.print_exc()

def test_simple_cases():
    """Test very simple cases."""
    print("\n" + "="*80)
    print("SIMPLE PLAYFAIR TESTS")
    print("="*80)
    
    key = "MONARCHY"
    
    simple_tests = [
        "AB",
        "ABCD", 
        "ABCDE",
        "AA",  # Duplicate - should become AXA
        "THE",
    ]
    
    for plaintext in simple_tests:
        print(f"\nPlaintext: '{plaintext}' (len={len(plaintext)})")
        
        try:
            encrypted = playfair.encrypt(plaintext, key)
            print(f"  Encrypted: '{encrypted}' (len={len(encrypted)})")
            
            # Show Playfair square for debugging
            square = playfair.get_square_display(key)
            print(f"  {square.split(chr(10))[0]}")
            
        except Exception as e:
            print(f"  ERROR: {e}")

if __name__ == "__main__":
    test_known_examples()
    test_simple_cases()
