import requests
from io import BytesIO
import time

time.sleep(1)

test_cases = [
    'Hello World',
    'Hello, World!',
    'The Quick Brown Fox',
    'Email: test@example.com', 
    'CaSe MixEd TEXT',
    'Hello, World! How are you?'
]

print('API ENCRYPTION/DECRYPTION TEST')
print('='*50)

for test_string in test_cases:
    file_data = BytesIO(test_string.encode('utf-8'))
    
    # Encrypt
    response = requests.post(
        'http://localhost:8000/process?mode=encrypt',
        files={'file': ('test.txt', file_data)},
    )
    result = response.json()
    
    if result.get('success'):
        # Read encrypted
        with open(f'outputs/{result["filename"]}', 'r') as f:
            encrypted = f.read()
        
        # Decrypt
        file_data = BytesIO(encrypted.encode('utf-8'))
        response2 = requests.post(
            'http://localhost:8000/process?mode=decrypt',
            files={'file': (result['filename'], file_data)},
        )
        result2 = response2.json()
        
        if result2.get('success'):
            with open(f'outputs/{result2["filename"]}', 'r') as f:
                decrypted = f.read()
            
            match = 'OK' if decrypted == test_string else 'FAIL'
            print(f'{match}: {test_string}')
            if match == 'FAIL':
                print(f'     Got: {decrypted}')
    else:
        print(f'ERROR encrypting: {test_string}')

print('='*50)
