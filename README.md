# 3-Layer File Encryption System

A complete file encryption/decryption system using a 3-layer cryptographic pipeline:
1. **Playfair Cipher** (substitution)
2. **Columnar Transposition** (transposition)
3. **DES Block Cipher** (block encryption)

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Initialize Encryption Keys
Run this ONCE to generate and save the system keys to `.keys.json`:
```bash
python -m backend.keys --init
```

**Important:** Keep `.keys.json` safe! It's in `.gitignore` but contains all encryption keys.

### 3. Install Testing Dependencies (Optional)
```bash
pip install pytest pytest-asyncio pytest-cov
```

### 4. Start the Web Application
```bash
python app.py
```

The application will start on `http://localhost:8000`

**API Documentation:**
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## System Architecture

### 3-Layer Pipeline

```
┌─────────────────────────────────────────────────────┐
│                    ENCRYPTION FLOW                   │
├─────────────────────────────────────────────────────┤
│                                                      │
│  Plaintext                                          │
│      ↓                                              │
│  [Layer 1: Playfair Cipher]                         │
│    • 5×5 Polybius square                            │
│    • Digraph substitution                           │
│    • I/J merged (25 letters)                       │
│      ↓                                              │
│  [Layer 2: Columnar Transposition]                  │
│    • Column reordering via key                      │
│    • Row-write, column-read                         │
│    • Aligned with Playfair output                   │
│      ↓                                              │
│  [Layer 3: DES Block Cipher]                        │
│    • 8-byte blocks (64-bit key)                     │
│    • ECB mode operation                             │
│    • PKCS7 padding                                  │
│      ↓                                              │
│  Ciphertext (Hex-encoded)                           │
│                                                      │
└─────────────────────────────────────────────────────┘
```

### Decryption Flow

Reverses all steps in order:
1. DES decryption (hex → text)
2. Columnar transposition reversal
3. Playfair substitution reversal

---

## API Endpoints

### File Operations

#### `POST /api/encrypt`
Upload and encrypt a file.

**Request:**
```
multipart/form-data:
  file: <binary data>
```

**Response:**
- Status 200: Encrypted file download
- Status 400/500: JSON error message

**Allowed file types:** `.txt`, `.log`, `.csv`, `.json`, `.md`

**Example (curl):**
```bash
curl -F "file=@plaintext.txt" http://localhost:5000/api/encrypt -o plaintext.txt.encrypted
```

#### `POST /api/decrypt`
Upload and decrypt a file.

**Request:**
```
multipart/form-data:
  file: <encrypted file>
```

**Response:**
- Status 200: Decrypted file download
- Status 400/500: JSON error message

**Example (curl):**
```bash
curl -F "file=@plaintext.txt.encrypted" http://localhost:5000/api/decrypt -o plaintext_decrypted.txt
```

### Text Operations (Testing)

#### `POST /api/encrypt-text`
Encrypt a text string (useful for testing).

**Request:**
```json
{
  "text": "HELLO WORLD"
}
```

**Response:**
```json
{
  "status": "success",
  "plaintext": "HELLO WORLD",
  "ciphertext": "hex-encoded-output...",
  "size_increase": "2.5x"
}
```

#### `POST /api/decrypt-text`
Decrypt a hex-encoded ciphertext.

**Request:**
```json
{
  "ciphertext": "hex-encoded-input..."
}
```

**Response:**
```json
{
  "status": "success",
  "plaintext": "HELLO WORLD",
  "ciphertext": "hex-encoded-input..."
}
```

### System

#### `GET /api/status`
Check system status and key information.

**Response:**
```json
{
  "status": "ready",
  "pipeline": "3-layer (Playfair → Columnar → DES)",
  "keys_loaded": true,
  "playfair_key_length": 12,
  "columnar_key_length": 9,
  "des_key_length": 16,
  "max_file_size_mb": 10.0
}
```

---

## Usage Examples

### Using Python Directly

#### Encrypt Text
```python
from backend import pipeline

plaintext = "HELLO WORLD"
ciphertext = pipeline.encrypt_text(plaintext)
print(f"Encrypted: {ciphertext}")
```

#### Decrypt Text
```python
from backend import pipeline

ciphertext = "..."  # from above
plaintext = pipeline.decrypt_text(ciphertext)
print(f"Decrypted: {plaintext}")
```

#### Encrypt/Decrypt File
```python
from backend import file_io

# Encrypt with metadata
result = file_io.encrypt_file_with_metadata("input.txt", "outputs")
print(result)

# Decrypt with metadata
result = file_io.decrypt_file_with_metadata(result['output_file'])
print(result)
```

**Using Web Interface (FastAPI + Swagger UI):**

1. Start the server: `python app.py`
2. Open `http://localhost:8000` for the web interface
3. Or go to `http://localhost:8000/docs` for interactive API docs
4. Choose a file to encrypt or decrypt
5. Downloaded encrypted/decrypted file

Or test with text:
1. Enter text in "Test Text Encryption" section
2. Click Encrypt/Decrypt
3. Results shown immediately

---

## File Structure

```
File_Encrypt/
├── app.py                          # Flask web application
├── requirements.txt                # Python dependencies
├── .keys.json                      # Encryption keys (auto-generated, git-ignored)
│
├── backend/
│   ├── __init__.py
│   ├── keys.py                     # Key generation & loading
│   ├── playfair.py                 # Layer 1: Playfair cipher
│   ├── columnar.py                 # Layer 2: Columnar transposition
│   ├── des_cipher.py               # Layer 3: DES block cipher
│   ├── pipeline.py                 # 3-layer pipeline orchestration
│   └── file_io.py                  # File operations with metadata
│
├── frontend/
│   ├── static/
│   │   ├── app.js                  # JavaScript UI logic
│   │   └── style.css               # CSS styling
│   └── templates/
│       └── index.html              # Web interface
│
├── uploads/                        # Temporary upload storage
├── outputs/                        # Encrypted/decrypted files
└── tests/                          # Unit tests (optional)
```

---

## Testing

FastAPI provides excellent built-in testing support. All tests use the `TestClient` from FastAPI, requiring no live server.

**Quick Start:**
```bash
# Run all tests
pytest tests/ -v

# Run with coverage report
pytest tests/ --cov=backend --cov=app --cov-report=html

# Run tests matching pattern
pytest tests/ -k "encrypt" -v
```

**Available Test Files:**
- `tests/test_api.py` - Comprehensive test suite (38 tests)
- `tests/examples.py` - Annotated examples for learning
- `tests/conftest.py` - Pytest configuration and shared fixtures

**Documentation:**
- [TESTING.md](TESTING.md) - Complete testing guide with patterns
- [TESTING_QUICK_REFERENCE.md](TESTING_QUICK_REFERENCE.md) - Quick lookup
- [FASTAPI_TESTING_FEATURES.md](FASTAPI_TESTING_FEATURES.md) - All features explained

**Test Coverage:**
- 38 tests total
- All 5 API endpoints
- All 3 encryption layers
- Error handling & validation
- Round-trip encryption/decryption
- File operations & edge cases

See [TESTING.md](TESTING.md) for comprehensive guide.

---

### Layer 1: Playfair Cipher

**How it works:**
- Builds a 5×5 grid (Polybius square) from the key
- Processes plaintext as digraphs (letter pairs)
- Rules for each digraph:
  - Same row: Shift right (wrap around)
  - Same column: Shift down (wrap around)
  - Rectangle: Swap columns
  - Duplicates in pair: Insert 'X' filler
  - Odd-length text: Pad with 'X'

**Key:** 12 random uppercase letters (no repeats)

**Example:**
```
Key: MONARCHY
Square:
M O N A R
C H Y B D
E F G I K
L P Q S T
U V W X Z

Plaintext:  INSTRUMENTS
Encrypted:  GFHFXGDGJIS
```

### Layer 2: Columnar Transposition

**How it works:**
- Takes Playfair output (uppercase letters)
- Determines column order from key alphabetical rank
- Writes plaintext row-by-row
- Reads columns in key-determined order

**Key:** 9 random uppercase letters

**Example:**
```
Key: SECRET

Column order: S(4) E(1) C(2) R(3) E(1) T(5)
              → sorted: E=1, C=2, R=3, S=4, T=5

Original (row-write):
S E C R E T
-----------
[row 1]
[row 2]

Read by column order (1,2,3,4,5):
Column 1, Column 2, Column 3, Column 4, Column 5
```

### Layer 3: DES Block Cipher

**How it works:**
- Industry-standard block cipher (DES)
- 64-bit blocks (8 bytes)
- 56-bit effective key (from 64-bit input)
- ECB mode (Electronic Codebook) for academic purposes
- PKCS7 padding for block alignment

**Key:** 16-character hex string (8 bytes)

**Note:** DES is legacy and only included for academic requirements. For production, use AES-256.

---

## Security Notes

### Academic Use Only

This system is designed for **educational purposes** and demonstrates:
- How symmetric encryption works
- Multi-layer cipher composition
- Block cipher operation

**Not suitable for production** due to:
- Playfair: Vulnerable to frequency analysis
- Columnar: Can be broken with large ciphertexts
- DES: 56-bit key is too small (breakable in hours with modern hardware)

### Protection Recommendations

For actual sensitive data, use:
- **AES-256** instead of DES
- **Modern block modes** like CBC or GCM (not ECB)
- **Key derivation** functions (PBKDF2, Argon2)
- **Message authentication** (HMAC or authenticated encryption)

---

## Troubleshooting

### "Key file not found" Error
**Solution:** Run `python -m backend.keys --init` first

### File Upload Size Exceeded
**Solution:** Maximum file size is 10 MB (configurable in `app.py`)

### Decryption Produces Garbage
**Possible causes:**
- Wrong key file (regenerate with `--init`)
- File corrupted during transmission
- Unsupported file encoding

### Server Won't Start
**Check:**
- Port 5000 is available: `netstat -an | findstr 5000`
- Dependencies installed: `pip list | grep -E "Flask|pycryptodome"`
- Python version 3.7+ installed: `python --version`

---

## API Usage Examples

### Using cURL

**Encrypt file:**
```bash
curl -F "file=@document.txt" \
  http://localhost:8000/api/encrypt \
  -o document.txt.encrypted
```

**Decrypt file:**
```bash
curl -F "file=@document.txt.encrypted" \
  http://localhost:8000/api/decrypt \
  -o document.txt
```

**Test encryption:**
```bash
curl -X POST http://localhost:8000/api/encrypt-text \
  -H "Content-Type: application/json" \
  -d '{"text":"HELLO"}' | jq
```

**Check status:**
```bash
curl http://localhost:8000/api/status | jq
```

### Using Python Requests

```python
import requests

# Upload file for encryption
with open('plaintext.txt', 'rb') as f:
    files = {'file': f}
    response = requests.post('http://localhost:8000/api/encrypt', files=files)
    
with open('plaintext.txt.encrypted', 'wb') as f:
    f.write(response.content)

# Test text encryption
response = requests.post('http://localhost:8000/api/encrypt-text', 
    json={"text": "HELLO WORLD"})
result = response.json()
print(result['ciphertext_full'])
```

---

## Development & Testing

### Run Pipeline Tests
```python
python -m backend.pipeline
```

### Test Playfair Cipher
```python
python -m backend.playfair
```

### Test Columnar Cipher
```python
python -m backend.columnar
```

### Test DES Cipher
```python
python -m backend.des_cipher
```

### Test File I/O
```python
python -m backend.file_io
```

### FastAPI Testing Features Used

This project uses FastAPI's built-in testing capabilities:

**TestClient:**
- Makes HTTP requests without running a server
- Provides full access to request/response details
- Can inspect headers, body, status codes

**Pytest Integration:**
- `@pytest.fixture` for reusable test data
- Parametrized testing with `@pytest.mark.parametrize`
- Class-based test organization
- Setup/teardown with fixtures

**Features Demonstrated:**
- Testing endpoints with different HTTP methods
- File upload testing
- JSON request/response body testing
- Error status code validation
- Round-trip encryption/decryption verification
- Performance testing
- Fixture dependency injection
- Test cleanup and resources

See [TESTING.md](TESTING.md) for full documentation on:
- How to write tests
- Using fixtures effectively
- Testing patterns and best practices
- Parametrized testing
- Coverage reports
- CI/CD integration

---

## Performance

### Speed Benchmarks (approximate)

| Operation | Time | Notes |
|-----------|------|-------|
| Encrypt 1KB text | 5-10ms | Playfair dominates |
| Encrypt 100KB text | 500-800ms | DES blocks (8 bytes) |
| Encrypt 1MB file | 5-8s | Network included |
| Decrypt 1MB file | 5-8s | Reverse pipeline |

### Expansion Ratio

- Playfair: 0-5% (substitution only, same length)
- Columnar: 0% (transposition only, same length)
- DES: ~30-35% (hex encoding: 1 byte → 2 chars + padding)

Final ciphertext is typically **2-3x** larger than plaintext (due to hex encoding).

---

## Future Enhancements

- [ ] Add AES-256 as Layer 3 option
- [ ] Implement CBC/GCM modes
- [ ] Add file compression before encryption
- [ ] Multi-file batch processing
- [ ] Key management UI (rotate, backup)
- [ ] Performance profiling & optimization
- [ ] Docker containerization
- [ ] REST API authentication (JWT)
- [ ] File streaming for large files (>100MB)
- [ ] Progress indicators for long operations

---

## License

This project is for educational purposes. See `LICENSE` file for details.

---

## Support

For issues or questions:
1. Check this README
2. Review code comments
3. Run diagnostic tests
4. Check system status endpoint

---

**Last Updated:** April 2, 2026
**Version:** 3.0 (3-Layer Pipeline)
**Framework:** FastAPI + Uvicorn
