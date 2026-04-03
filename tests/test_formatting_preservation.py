"""
Test formatting preservation in encryption/decryption
Tests that spaces, punctuation, and case are preserved after decryption
"""

from backend import pipeline

TEST_CASES = [
    "Hello World",
    "The Quick Brown Fox",
    "Hello, World!",
    "This is a test.",
    "CaSe MixEd TEXT",
    "Multiple   spaces",
    "with-dashes and_underscores",
    "Email: test@example.com",
]

print("=" * 80)
print("FORMATTING PRESERVATION TEST")
print("=" * 80)

for i, plaintext in enumerate(TEST_CASES, 1):
    print(f"\n[Test {i}] Input: {repr(plaintext)}")
    
    try:
        # Encrypt
        ciphertext = pipeline.encrypt_text(plaintext)
        print(f"  Encrypted: {ciphertext[:60]}...")
        
        # Decrypt
        decrypted = pipeline.decrypt_text(ciphertext)
        print(f"  Decrypted: {repr(decrypted)}")
        
        # Check if they match
        if decrypted == plaintext:
            print(f"  ✅ PERFECT MATCH - Formatting preserved!")
        else:
            print(f"  ⚠️  DIFFERENCE:")
            print(f"      Input:     {repr(plaintext)}")
            print(f"      Output:    {repr(decrypted)}")
            
    except Exception as e:
        print(f"  ❌ ERROR: {e}")

print("\n" + "=" * 80)
