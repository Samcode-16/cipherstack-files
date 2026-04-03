from backend.playfair import encrypt, decrypt

key = 'MONARCHY'
plaintext = 'INSTRUMENTS'

enc = encrypt(plaintext, key)
dec = decrypt(enc, key)

print(f'Playfair test with MONARCHY key')
print(f'Plaintext: {plaintext}')
print(f'Encrypted: {enc}')
print(f'Decrypted: {dec}')
print(f'Match: {dec.rstrip("X") == plaintext}')
