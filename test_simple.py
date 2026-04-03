"""
Simple step-by-step test with debugging
"""
import requests
from pathlib import Path

BASE_URL = "http://localhost:8000"

# Create test file
plaintext = "TEST"
Path("t.txt").write_text(plaintext)

# Encrypt
print("\n[ENCRYPT]")
with open("t.txt", 'rb') as f:
    # When using 'file' as the key, the filename comes from the file object
    r = requests.post(f"{BASE_URL}/process", files={'file': ('t.txt', f)}, data={'mode': 'encrypt'})
    enc_fn = r.json()['filename']
    print(f"Result filename: {enc_fn}")

# Get encrypted content
enc_file = Path("outputs") / enc_fn
enc_content = enc_file.read_text()
print(f"Encrypted content: {enc_content[:40]}...")

# Decrypt - IMPORTANT: Explicitly pass the filename!
print("\n[DECRYPT]")  
with open(enc_file, 'rb') as f:
    # IMPORTANT: Explicitly pass the filename so FastAPI knows it's a .encrypted file
    r = requests.post(f"{BASE_URL}/process", files={'file': (enc_fn, f)}, data={'mode': 'decrypt'})
    print(f"  Sent filename: {enc_fn}")
    dec_fn = r.json()['filename']
    print(f"  Result filename: {dec_fn}")

# Get decrypted content
dec_file = Path("outputs") / dec_fn
dec_content = dec_file.read_text()
print(f"Decrypted content: {repr(dec_content)}")

# Cleanup
Path("t.txt").unlink()
