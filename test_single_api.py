import requests
from io import BytesIO
import time

time.sleep(2)

test_string = 'Hello World'
print(f'Testing: {test_string}')

file_data = BytesIO(test_string.encode('utf-8'))

# Encrypt
print('Encrypting...')
response = requests.post(
    'http://localhost:8000/process?mode=encrypt',
    files={'file': ('test.txt', file_data)},
    timeout=5
)
print(f'Encrypt response: {response.status_code}')
result = response.json()
print(f'Encrypt result: {result}')

if result.get('success'):
    with open(f'outputs/{result["filename"]}', 'r') as f:
        encrypted = f.read()
    print(f'Encrypted file content (first 80 chars): {encrypted[:80]}')
    
    # Decrypt
    print('Decrypting...')
    file_data = BytesIO(encrypted.encode('utf-8'))
    response2 = requests.post(
        'http://localhost:8000/process?mode=decrypt',
        files={'file': (result['filename'], file_data)},
        timeout=5
    )
    print(f'Decrypt response: {response2.status_code}')
    result2 = response2.json()
    print(f'Decrypt result: {result2}')
    
    if result2.get('success'):
        with open(f'outputs/{result2["filename"]}', 'r') as f:
            decrypted = f.read()
        print(f'Decrypted: {decrypted}')
        print(f'Match: {decrypted == test_string}')
