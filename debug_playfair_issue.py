from backend.keys import load_keys
from backend.playfair import _prepare_plaintext, _build_square

keys = load_keys()
pf_key = keys["playfair"]
print(f'Playfair key: {pf_key}')
print(f'Has J: {"J" in pf_key}')
print(f'Key length: {len(pf_key)}')

# Check what _prepare_plaintext does
digraphs = _prepare_plaintext("HELLO")
print(f'\nDigraphs for HELLO: {digraphs}')

# Check square
square = _build_square(pf_key)
print(f'\nPlayfair square built successfully: {len(square)}x{len(square[0])}')

# Manual encryption test
from backend.playfair import encrypt, decrypt
enc = encrypt("HELLO", pf_key)
print(f'\nEncrypt("HELLO") = {enc}')
dec = decrypt(enc, pf_key)
print(f'Decrypt("{enc}") = {dec}')
