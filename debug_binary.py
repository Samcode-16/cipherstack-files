from backend.pipeline import encrypt_text, decrypt_text

test = 'BINARY:SGVsbG8gV29ybGQ='
print('IN length :', len(test))
ct = encrypt_text(test)
print('CT length :', len(ct))
dt = decrypt_text(ct)
print('OUT length:', len(dt))
print('IN :', test)
print('OUT:', dt)
print('MATCH:', test == dt)
