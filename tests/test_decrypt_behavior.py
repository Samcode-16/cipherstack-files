"""
Test what happens when we pass different inputs to decrypt_text()
"""

from backend import pipeline

# Test 1: Correct encrypted hex
plaintext = "Hello World"
encrypted_hex = pipeline.encrypt_text(plaintext)
print(f"[Test 1] Correct encrypted hex")
print(f"  Input: {encrypted_hex[:50]}...")
try:
    result = pipeline.decrypt_text(encrypted_hex)
    print(f"  Output: {repr(result)}")
    print(f"  ✅ SUCCESS")
except Exception as e:
    print(f"  ❌ ERROR: {e}")

# Test 2: What if the decimal version is passed?
plaintext_text = "Hello World"
print(f"\n[Test 2] Plaintext (not encrypted)")
print(f"  Input: {repr(plaintext_text)}")
try:
    result = pipeline.decrypt_text(plaintext_text)
    print(f"  Output: {repr(result)}")
except Exception as e:
    print(f"  ❌ ERROR: {e}")
    print(f"  Error type: {type(e).__name__}")
    print(f"  Error msg: {str(e)}")

# Test 3: What if we accidentally encrypt the hex string?
print(f"\n[Test 3] Double encryption (encrypting the hex string)")
encrypted_hex2 = pipeline.encrypt_text(encrypted_hex)
print(f"  Encrypted the hex string: {encrypted_hex2[:50]}...")
print(f"  If we then decrypt this...")
try:
    result = pipeline.decrypt_text(encrypted_hex2)
    print(f"  Output: {repr(result[:50])}...")  # Show first 50 chars
except Exception as e:
    print(f"  ERROR: {e}")
