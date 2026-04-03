"""
Simulate the exact frontend workflow:
1. User selects plaintext file
2. Clicks "Encrypt" → downloads .encrypted file
3. User selects the .encrypted file
4. Clicks "Decrypt" → should get plain text back

This mimics what happens in the /process endpoint
"""

from backend import pipeline
from pathlib import Path

print("=" * 80)
print("SIMULATING FRONTEND FILE WORKFLOW")
print("=" * 80)

# Step 1: Encrypt a plaintext file
plaintext = "Hello World! This is a test message."
print(f"\n[Step 1] Original text: {repr(plaintext)}")

encrypted_hex = pipeline.encrypt_text(plaintext)
print(f"[Step 1] Encrypted (hex): {encrypted_hex[:60]}...")

# Step 2: Simulate saving to .encrypted file
temp_encrypted_file = Path("temp_test.encrypted")
temp_encrypted_file.write_text(encrypted_hex, encoding='utf-8')
print(f"[Step 2] Saved to file: {temp_encrypted_file}")

# Step 3: Simulate reading the .encrypted file (as user would upload)
file_content = temp_encrypted_file.read_text(encoding='utf-8')
print(f"[Step 3] Read from file: {file_content[:60]}...")

# Step 4: Test - what happens if we accidentally encrypt again?
double_encrypted = pipeline.encrypt_text(file_content)
print(f"\n[PROBLEM TEST] If we ENCRYPT the hex string:")
print(f"  Input: {file_content[:60]}...")
print(f"  Output: {double_encrypted[:60]}...")
print(f"  This looks like 'encrypted again'!\n")

# Step 5: Decrypt correctly
decrypted = pipeline.decrypt_text(file_content)
print(f"[Step 5] Decrypted: {repr(decrypted)}")

# Step 6: Test recovery
normalized_original = "HELLOWORLD"  # Playfair removes spaces/punctuation
if decrypted == normalized_original:
    print(f"✅ Decryption SUCCESS")
else:
    print(f"❌ Decryption FAILED")
    print(f"   Expected (normalized): {repr(normalized_original)}")
    print(f"   Got: {repr(decrypted)}")

# Clean up
temp_encrypted_file.unlink()

print("\n" + "=" * 80)
print("HYPOTHESIS: User might be clicking 'Encrypt' instead of 'Decrypt'")
print("That would explain 'different encrypted' output!")
print("=" * 80)
