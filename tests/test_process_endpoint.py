"""
Test the /process endpoint with actual HTTP requests
Simulates: 
1. Encrypt a file
2. Download the encrypted file
3. Decrypt the encrypted file
4. Check the results
"""

import requests
import json
from pathlib import Path

BASE_URL = "http://localhost:8000"

# Test plaintext
plaintext = "Hello World"

print("=" * 80)
print("TESTING /process ENDPOINT")
print("=" * 80)

# Step 1: Create a temp plaintext file
print(f"\n[Step 1] Creating plaintext file: {repr(plaintext)}")
temp_plaintext = Path("temp_plaintext.txt")
temp_plaintext.write_text(plaintext, encoding='utf-8')
print(f"  ✓ Created: {temp_plaintext}")

# Step 2: Encrypt via /process endpoint
print(f"\n[Step 2] Submitting to /process with mode='encrypt'")
with open(temp_plaintext, 'rb') as f:
    files = {'file': (temp_plaintext.name, f, 'text/plain')}
    data = {'mode': 'encrypt'}
    
    try:
        resp = requests.post(f"{BASE_URL}/process", files=files, data=data)
        print(f"  Status: {resp.status_code}")
        print(f"  Response: {resp.json()}")
        
        if resp.json().get('success'):
            encrypted_filename = resp.json()['filename']
            print(f"  ✓ Encrypted file: {encrypted_filename}")
            
            # Get the encrypted content from outputs folder
            encrypted_file = Path("outputs") / encrypted_filename
            encrypted_content = encrypted_file.read_text(encoding='utf-8')
            print(f"  Encrypted content (first 60 chars): {encrypted_content[:60]}...")
            
            # Step 3: Decrypt the encrypted file
            print(f"\n[Step 3] Submitting encrypted file to /process with mode='decrypt'")
            with open(encrypted_file, 'rb') as ef:
                files = {'file': (encrypted_file.name, ef, 'application/octet-stream')}
                data = {'mode': 'decrypt'}
                
                decrypt_resp = requests.post(f"{BASE_URL}/process", files=files, data=data)
                print(f"  Status: {decrypt_resp.status_code}")
                print(f"  Response: {decrypt_resp.json()}")
                
                if decrypt_resp.json().get('success'):
                    decrypted_filename = decrypt_resp.json()['filename']
                    print(f"  ✓ Decrypted file: {decrypted_filename}")
                    
                    # Get the decrypted content
                    decrypted_file = Path("outputs") / decrypted_filename
                    decrypted_content = decrypted_file.read_text(encoding='utf-8')
                    print(f"  Decrypted content: {repr(decrypted_content)}")
                    
                    # Compare
                    normalized_plaintext = plaintext.upper().replace(" ", "")  # Playfair normalizes
                    if decrypted_content == normalized_plaintext:
                        print(f"\n✅ SUCCESS: Decryption works correctly!")
                    else:
                        print(f"\n❌ MISMATCH:")
                        print(f"   Expected: {repr(normalized_plaintext)}")
                        print(f"   Got: {repr(decrypted_content)}")
                else:
                    print(f"  ❌ Decrypt failed: {decrypt_resp.json()}")
        else:
            print(f"  ❌ Encryption failed: {resp.json()}")
    except requests.exceptions.ConnectionError:
        print("  ❌ Could not connect to server. Is it running on http://localhost:8000?")
    except Exception as e:
        print(f"  ❌ Error: {e}")

# Cleanup
temp_plaintext.unlink(missing_ok=True)

print("\n" + "=" * 80)
