from backend.playfair import encrypt, decrypt

key = 'WRLNPKBYXQSU'
plaintext = 'HELLO'

enc = encrypt(plaintext, key)
dec = decrypt(enc, key)

print(f'Playfair test with WRLNPKBYXQSU key')
print(f'Plaintext: {plaintext}')
print(f'Encrypted: {enc}')
print(f'Decrypted: {dec}')
print(f'Length check: plaintext={len(plaintext)}, encrypted={len(enc)}, decrypted={len(dec)}')

# Try decrypting other ciphertexts
print(f'\nManual test: decrypt IFNYRT')
result = decrypt('IFNYRT', key)
print(f'Result: {result}')

# Try different order of characters
print(f'\nTrying pairs manually:')
print(f'IF -> ?')
print(f'NY -> ?')
print(f'RT -> ?')
