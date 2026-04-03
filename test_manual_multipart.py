"""
Test with explicit inspection of the request
"""
import requests
from pathlib import Path

# Create test file
plaintext = "XXX"
Path("test.txt").write_text(plaintext)

# Encrypt
print("[ENCRYPT]")
with open("test.txt", 'rb') as f:
    r = requests.post(
        'http://localhost:8000/process',
        files={'file': ('test.txt', f)},
        data={'mode': 'encrypt'}
    )
    enc_fn = r.json()['filename']
    print(f"  Result: {enc_fn}")

#  Now decrypt
enc_file = Path("outputs") / enc_fn
print(f"\n[DECRYPT]")
print(f"  Uploading: {enc_fn}")

with open(enc_file, 'rb') as f:    
    # Build the request manually to see what's being sent
    from requests_toolbelt import MultipartEncoder
    
    m = MultipartEncoder(
        fields={'file': (enc_fn, f), 'mode': 'decrypt'}
    )
    
    r = requests.post(
        'http://localhost:8000/process',
        data=m,
        headers={'Content-Type': m.content_type}
    )
    dec_fn = r.json()['filename']
    print(f"  Result: {dec_fn}")

# Check the result
dec_file = Path("outputs") / dec_fn
result = dec_file.read_text()
print(f"  Content: {repr(result)}")

# Cleanup
Path("test.txt").unlink()
