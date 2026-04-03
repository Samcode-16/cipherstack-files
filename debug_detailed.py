#!/usr/bin/env python3
from backend import playfair, columnar, des_cipher
from backend.keys import load_keys

keys = load_keys()

plaintext = "HELLO"
pf_key = keys["playfair"]
col_key = keys["columnar"]
des_key = keys["des"]

print("="*60)
print(f"ENCRYPTION: Input = {repr(plaintext)}")
print("="*60)

# Layer 1
print(f"\n1. Playfair.encrypt({repr(plaintext)}, key)")
layer1_enc = playfair.encrypt(plaintext, pf_key)
print(f"   Output: {repr(layer1_enc)} (len={len(layer1_enc)})")

# Compute padding
col_padding = (len(col_key) - (len(layer1_enc) % len(col_key))) % len(col_key)
print(f"\n2. Columnar padding needed: {col_padding} (key_len={len(col_key)}, output_len={len(layer1_enc)})")

# Layer 2  
print(f"\n3. Columnar.encrypt({repr(layer1_enc)}, key)")
layer2_enc = columnar.encrypt(layer1_enc, col_key)
print(f"   output: {repr(layer2_enc)} (len={len(layer2_enc)})")

# Layer 3
print(f"\n4. DES.encrypt({repr(layer2_enc)}, key)")
layer3_enc = des_cipher.encrypt(layer2_enc, des_key)
print(f"   Output (hex): {layer3_enc[:32]}... (len={len(layer3_enc)})")

# Final with padding marker
final_enc = f"{col_padding:02x}" + layer3_enc
print(f"\n5. Final with padding marker: {final_enc[:20]}... (first 2 chars = padding)")

print("\n" + "="*60)
print("DECRYPTION")
print("="*60)

# Extract padding
padding_extracted = int(final_enc[:2], 16)
des_hex = final_enc[2:]
print(f"\n1. Extract padding: {padding_extracted}")

# Layer 3 decrypt
print(f"\n2. DES.decrypt(hex, key)")
layer3_dec = des_cipher.decrypt(des_hex, des_key)
print(f"   Output: {repr(layer3_dec)} (len={len(layer3_dec)})")

# Layer 2 decrypt
print(f"\n3. Columnar.decrypt({repr(layer3_dec)}, key)")
layer2_dec = columnar.decrypt(layer3_dec, col_key)
print(f"   Output: {repr(layer2_dec)} (len={len(layer2_dec)})")

# Remove padding
if padding_extracted > 0:
    layer2_unpadded = layer2_dec[:-padding_extracted]
    print(f"\n4. Remove {padding_extracted} chars padding: {repr(layer2_unpadded)} (len={len(layer2_unpadded)})")
else:
    layer2_unpadded = layer2_dec
    print(f"\n4. No padding to remove")

# Layer 1 decrypt
print(f"\n5. Playfair.decrypt({repr(layer2_unpadded)}, key)")
layer1_dec = playfair.decrypt(layer2_unpadded, pf_key)
print(f"   Output: {repr(layer1_dec)} (len={len(layer1_dec)})")

# Final cleanup
plaintext_recovered = layer1_dec.rstrip('X')
print(f"\n6. Strip trailing X: {repr(plaintext_recovered)}")

print(f"\n{'='*60}")
print(f"Result: {repr(plaintext)} -> {repr(plaintext_recovered)}")
print(f"Match: {plaintext == plaintext_recovered}")
