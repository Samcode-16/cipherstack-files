"""
Final comprehensive test of the fixed encryption/decryption flow
"""
import requests
from pathlib import Path

TEST_CASES = [
    "Hello World",
    "TEST",
    "The quick brown fox jumps over the lazy dog",
    "123 special chars !@#$%",
]

BASE_URL = "http://localhost:8000"
RESULTS = []

print("=" * 80)
print("COMPREHENSIVE ENCRYPTION/DECRYPTION TEST")
print("=" * 80)

for i, plaintext in enumerate(TEST_CASES, 1):
    print(f"\n[Test {i}] '{plaintext}'")
    
    # Create temp file
    test_file = Path(f"test_{i}.txt")
    test_file.write_text(plaintext)
    print(f"  ✓ Created test file")
    
    try:
        # Encrypt
        with open(test_file, 'rb') as f:
            r = requests.post(f"{BASE_URL}/process", files={'file': (test_file.name, f)}, params={'mode': 'encrypt'})
            if not r.json()['success']:
                print(f"  ❌ Encryption failed: {r.json()['error']}")
                continue
            enc_fn = r.json()['filename']
            print(f"  ✓ Encrypted to: {enc_fn}")
        
        # Get encrypted content
        enc_file = Path("outputs") / enc_fn
        enc_content = enc_file.read_text()
        print(f"  ✓ Encrypted content length: {len(enc_content)} chars")
        
        # Decrypt
        with open(enc_file, 'rb') as f:
            r = requests.post(f"{BASE_URL}/process", files={'file': (enc_fn, f)}, params={'mode': 'decrypt'})
            if not r.json()['success']:
                print(f"  ❌ Decryption failed: {r.json()['error']}")
                continue
            dec_fn = r.json()['filename']
            print(f"  ✓ Decrypted to: {dec_fn}")
        
        # Get decrypted content
        dec_file = Path("outputs") / dec_fn
        decrypted = dec_file.read_text()
        
        # Normalize plaintext (Playfair removes spaces, punctuation, numbers)
        normalized = ''.join(c.upper() for c in plaintext if c.isalpha())
        
        # Check result
        if decrypted == normalized:
            print(f"  ✅ SUCCESS: Decryption matches expected output")
            RESULTS.append((plaintext, True))
        else:
            print(f"  ❌ MISMATCH:")
            print(f"     Expected: {repr(normalized)}")
            print(f"     Got:      {repr(decrypted)}")
            RESULTS.append((plaintext, False))
    
    except Exception as e:
        print(f"  ❌ ERROR: {e}")
        RESULTS.append((plaintext, False))
    
    finally:
        test_file.unlink(missing_ok=True)

# Summary
print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
passed = sum(1 for _, success in RESULTS if success)
total = len(RESULTS)
print(f"Passed: {passed}/{total} ({100*passed//total}%)")
for plaintext, success in RESULTS:
    status = "✅" if success else "❌"
    print(f"  {status} {repr(plaintext[:40])}")
print("=" * 80)
