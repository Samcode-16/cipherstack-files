"""
Direct test of pipeline.decrypt_text() function
"""

from backend import pipeline

# Encrypt first
plaintext = "Hello World"
print(f"Original: {repr(plaintext)}")

encrypted_hex = pipeline.encrypt_text(plaintext)
print(f"Encrypted: {encrypted_hex[:60]}...")
print(f"Encrypted length: {len(encrypted_hex)}")

# Try to decrypt
try:
    decrypted = pipeline.decrypt_text(encrypted_hex)
    print(f"Decrypted: {repr(decrypted)}")
    print(f"Decrypted length: {len(decrypted)}")
    
    if decrypted == "HELLOWORLD":
        print("✅ SUCCESS")
    else:
        print(f"❌ Got different output: {repr(decrypted)}")
        
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
