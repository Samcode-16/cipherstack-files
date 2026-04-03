#!/usr/bin/env python3
"""
Debug script to trace where the corruption happens in the pipeline.
"""

from backend import pipeline, playfair, columnar, des_cipher
from backend.keys import load_keys
import re

def test_problematic_text():
    """Test the problematic text from test case 5."""
    print("="*80)
    print("DEBUGGING: Long text corruption")
    print("="*80)
    
    original_input = "The Quick Brown Fox Jumps Over The Lazy Dog"
    keys = load_keys()
    
    # Step 1: Normalize input
    normalized = re.sub(r"[^A-Za-z]", "", original_input).upper()
    print(f"\n1. Original input: '{original_input}'")
    print(f"   Normalized: '{normalized}'")
    print(f"   Length: {len(normalized)}")
    
    # Step 2: Playfair encryption
    pf_encrypted = playfair.encrypt(normalized, keys['playfair'])
    print(f"\n2. Playfair encrypted: '{pf_encrypted}'")
    print(f"   Length: {len(pf_encrypted)}")
    print(f"   Length difference: {len(pf_encrypted) - len(normalized)}")
    
    # Step 3: Playfair decryption
    pf_decrypted = playfair.decrypt(pf_encrypted, keys['playfair'])
    print(f"\n3. Playfair decrypted: '{pf_decrypted}'")
    print(f"   Length: {len(pf_decrypted)}")
    
    # Check what X's were added
    x_positions = [i for i, c in enumerate(pf_decrypted) if c == 'X']
    print(f"   X positions: {x_positions}")
    if x_positions:
        print(f"   X's found at positions: {', '.join(f'{i}({pf_decrypted[max(0,i-1):i+2]})' for i in x_positions)}")
    
    # Step 4: Remove fillers
    filler_removed = playfair.remove_fillers(pf_decrypted, len(normalized))
    print(f"\n4. After filler removal: '{filler_removed}'")
    print(f"   Length: {len(filler_removed)}")
    
    # Step 5: Compare
    print(f"\n5. Comparison:")
    print(f"   Original normalized: '{normalized}'")
    print(f"   After PF roundtrip:  '{filler_removed}'")
    print(f"   Match: {filler_removed == normalized}")
    
    if filler_removed != normalized:
        print(f"\n   Character-by-character differences:")
        for i, (orig, curr) in enumerate(zip(normalized, filler_removed)):
            if orig != curr:
                print(f"   Position {i}: '{orig}' → '{curr}'")
    
    # Full pipeline test
    print(f"\n6. Full pipeline test:")
    encrypted_full = pipeline.encrypt_text(original_input)
    decrypted_full = pipeline.decrypt_text(encrypted_full)
    
    print(f"   Encrypted: {encrypted_full[:64]}...")
    print(f"   Decrypted: '{decrypted_full}'")
    print(f"   Expected:  '{normalized}'")
    print(f"   Match: {decrypted_full == normalized}")

if __name__ == "__main__":
    test_problematic_text()
