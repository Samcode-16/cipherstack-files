from backend.keys import load_keys
from backend import playfair

keys = load_keys()
pf_key = keys['playfair']

# Test basic Playfair
plaintext = 'HELLO'
enc = playfair.encrypt(plaintext, pf_key)
dec = playfair.decrypt(enc, pf_key)

print(f'Playfair key: {pf_key}')
print(f'Plaintext: {repr(plaintext)}')
print(f'Encrypted: {repr(enc)} (len={len(enc)})')
print(f'Decrypted: {repr(dec)} (len={len(dec)})')
print(f'Match: {dec.rstrip("X") == plaintext.upper()}')
