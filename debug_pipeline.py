#!/usr/bin/env python3
from backend import playfair, columnar, des_cipher
from backend.keys import load_keys

keys = load_keys()

# Step-by-step test
plaintext = "HELLO"
pf_key = keys["playfair"]
col_key = keys["columnar"]
des_key = keys["des"]

print(f"Step 1 - Playfair encrypt: '{plaintext}' with key '{pf_key}'")
layer1 = playfair.encrypt(plaintext, pf_key)
print(f"  Output: '{layer1}' (len={len(layer1)})")

print(f"\nStep 2 - Columnar encrypt: '{layer1}' with key '{col_key}'")
layer2 = columnar.encrypt(layer1, col_key)
print(f"  Output: '{layer2}' (len={len(layer2)})")

print(f"\nStep 3 - DES encrypt: '{layer2}' with key '{des_key}'")
layer3 = des_cipher.encrypt(layer2, des_key)
print(f"  Output: '{layer3[:50]}...' (len={len(layer3)})")

print(f"\n--- DECRYPTION ---")
print(f"Step 3 - DES decrypt: hex input (len={len(layer3)})")
dec_layer2 = des_cipher.decrypt(layer3, des_key)
print(f"  Output: '{dec_layer2}' (len={len(dec_layer2)})")

print(f"\nStep 2 - Columnar decrypt: '{dec_layer2}' with key '{col_key}'")
dec_layer1 = columnar.decrypt(dec_layer2, col_key)
print(f"  Output: '{dec_layer1}' (len={len(dec_layer1)})")

print(f"\nStep 1 - Playfair decrypt: '{dec_layer1}' with key '{pf_key}'")
try:
    plaintext_recovered = playfair.decrypt(dec_layer1, pf_key)
    plaintext_recovered = plaintext_recovered.rstrip('X')
    print(f"  Output: '{plaintext_recovered}' (len={len(plaintext_recovered)})")
    print(f"  Match: {plaintext_recovered.upper() == plaintext.upper()}")
except Exception as e:
    print(f"  ERROR: {e}")
    print(f"  Input to playfair.decrypt has length {len(dec_layer1)}")
