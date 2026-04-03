"""
Test script to identify the decryption issue.
Simulates: encrypt file → download → re-upload for decryption
"""

from backend import pipeline
from pathlib import Path
import json

# Test cases
test_texts = [
    "Hello World",
    "HELLO",
    "The quick brown fox",
    "Test message 123",
]

print("=" * 80)
print("TESTING ENCRYPTION/DECRYPTION ROUNDTRIP")
print("=" * 80)

for idx, plaintext in enumerate(test_texts, 1):
    print(f"\n[Test {idx}] Input: {repr(plaintext)}")
    print(f"  Length: {len(plaintext)}")
    
    try:
        # Step 1: Encrypt
        ciphertext = pipeline.encrypt_text(plaintext)
        print(f"  ✓ Encrypted to: {ciphertext[:50]}...")
        print(f"    Hex length: {len(ciphertext)}")
        
        # Step 2: Simulate saved file content (what gets written to .encrypted file)
        encrypted_file_content = ciphertext  # This is what gets saved
        print(f"  ℹ File content: {encrypted_file_content[:50]}...")
        
        # Step 3: Simulate reading from encrypted file
        # (User uploads the .encrypted file, which contains the hex string)
        decryption_input = encrypted_file_content
        print(f"  ℹ Decryption input: {decryption_input[:50]}...")
        
        # Step 4: Decrypt
        recovered = pipeline.decrypt_text(decryption_input)
        print(f"  ✓ Decrypted to: {repr(recovered)}")
        
        # Step 5: Compare
        if recovered == plaintext:
            print(f"  ✅ SUCCESS - Perfect match!")
        else:
            print(f"  ❌ MISMATCH!")
            print(f"     Expected: {repr(plaintext)}")
            print(f"     Got:      {repr(recovered)}")
            
    except Exception as e:
        print(f"  ❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

print("\n" + "=" * 80)
