#!/usr/bin/env python3
"""
Test Playfair cipher directly to identify the issue.
"""

from backend import playfair
from backend.keys import load_keys

def test_playfair_direct():
    """Test Playfair encryption/decryption directly."""
    keys = load_keys()
    pf_key = keys['playfair']
    
    test_cases = [
        "HELLO",
        "HELLOWORLD",
        "THEQUICKBROWN",
        "FOXJUMPS",
        "THEQUICKBROWNFOXJUMPSOVERTHELAZYDOG",
    ]
    
    print("="*80)
    print("PLAYFAIR CIPHER DIRECT TEST")
    print(f"Key: {pf_key}")
    print("="*80)
    
    for test_input in test_cases:
        print(f"\nTest input: '{test_input}' (len={len(test_input)})")
        
        try:
            encrypted = playfair.encrypt(test_input, pf_key)
            print(f"  Encrypted: '{encrypted}' (len={len(encrypted)})")
            
            decrypted = playfair.decrypt(encrypted, pf_key)
            print(f"  Decrypted: '{decrypted}' (len={len(decrypted)})")
            
            # Check result
            if decrypted == test_input:
                print(f"  ✓ PASS - Perfect roundtrip")
            else:
                print(f"  ✗ FAIL - Mismatch!")
                print(f"    Expected:  '{test_input}'")
                print(f"    Got:       '{decrypted}'")
                
                # Show differences
                for i, (e, g) in enumerate(zip(test_input, decrypted)):
                    if e != g:
                        print(f"    Pos {i}: '{e}' → '{g}'")
        
        except Exception as e:
            print(f"  ✗ ERROR: {e}")

if __name__ == "__main__":
    test_playfair_direct()
