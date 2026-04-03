# 🚀 How to Run Your Encryption Pipeline System

Complete step-by-step guide to get your 3-layer encryption system running.

---

## Step 1: Install Dependencies

### Using the Virtual Environment (Already Created)

```bash
cd d:\BCA\4th_sem\File_Encrypt

# Activate virtual environment
.venv\Scripts\activate

# Install all dependencies
pip install -r requirements.txt
```

**Expected output:**
```
Successfully installed fastapi-0.104.1 uvicorn-0.24.0 pycryptodome-3.18.0 pytest-7.4.3 ...
```

---

## Step 2: Generate Encryption Keys (First Time Only)

Run this command to generate and save the encryption keys:

```bash
python backend/keys.py --init
```

**What it does:**
- Generates a random Playfair key (12 letters)
- Generates a random Columnar key (9 letters)
- Generates a random DES key (16 hex characters)
- Saves all keys to `.keys.json` (git-ignored for security)

**Expected output:**
```
[keys] Keys written to d:\BCA\4th_sem\File_Encrypt\.keys.json  (permissions: 600)
```

**If you see an error:**
Try this alternative:
```bash
python -c "from backend.keys import generate_keys, save_keys; save_keys(generate_keys())"
```

---

## Step 3: Start the FastAPI Server

```bash
python app.py
```

**Expected output:**
```
[app] ✓ Keys loaded successfully
[app] Starting FastAPI server on http://localhost:8000
[app] API docs available at http://localhost:8000/docs
[app] Alternative docs at http://localhost:8000/redoc

INFO:     Uvicorn running on http://0.0.0.0:8000
```

The server is now running! ✅

---

## Step 4: Access the Web Interface

### Option A: Web UI (Recommended for Users)
Open your browser and go to:
```
http://localhost:8000
```

You'll see:
- 📤 File encryption form
- 📥 File decryption form
- 🧪 Test text encryption/decryption
- ℹ️ Pipeline information

### Option B: Swagger API Docs (Best for Testing)
```
http://localhost:8000/docs
```

Features:
- ✅ Interactive API testing
- ✅ "Try it out" buttons for each endpoint
- ✅ Automatic request/response examples
- ✅ Full parameter documentation

### Option C: ReDoc (Alternative Documentation)
```
http://localhost:8000/redoc
```

Features:
- ✅ Beautiful documentation
- ✅ Full endpoint descriptions
- ✅ Request/response schema details

---

## Step 5: Test the System

### Via Web UI (http://localhost:8000)

**Test Encryption:**
1. Click on "Test Text Encryption" section
2. Enter text: `HELLO WORLD`
3. Click "Encrypt"
4. See the hex-encoded ciphertext
5. Ciphertext automatically copies to decrypt field

**Test Decryption:**
1. Ciphertext should already be in the field
2. Click "Decrypt"
3. See original text recovered: `HELLO WORLD`

**Test File Encryption:**
1. Create a test file (test.txt with some content)
2. Choose file in "Encrypt File" section
3. Click "🔒 Encrypt File"
4. Download the encrypted file (name.txt.encrypted)

**Test File Decryption:**
1. Choose the encrypted file
2. Click "🔓 Decrypt File"
3. Download the decrypted file
4. Verify content matches original

### Via Swagger UI (http://localhost:8000/docs)

**Test Encryption Endpoint:**
1. Scroll to `/api/encrypt-text` (POST)
2. Click "Try it out"
3. Enter in request body:
   ```json
   {
     "text": "HELLO WORLD"
   }
   ```
4. Click "Execute"
5. See response with ciphertext

**Example Response:**
```json
{
  "status": "success",
  "plaintext": "HELLO WORLD",
  "ciphertext": "65a8c0f1...",
  "ciphertext_full": "65a8c0f1e3d4...",
  "size_increase": "3.45x"
}
```

---

## Complete Workflow Example

### Scenario: Encrypt and Decrypt a File

```
1. START server
   $ python app.py
   [app] ✓ Keys loaded successfully
   [app] Starting FastAPI server on http://localhost:8000

2. OPEN browser
   http://localhost:8000

3. CREATE test file
   Create: secret.txt
   Content: "This is my secret message!"

4. ENCRYPT file
   - Choose secret.txt
   - Click "🔒 Encrypt File"
   - Download: secret.txt.encrypted

5. DECRYPT file
   - Choose secret.txt.encrypted
   - Click "🔓 Decrypt File"
   - Download: decrypted_secret.txt.encrypted
   - Verify: Content matches original!

6. VIEW pipeline info
   - See how 3 layers work together
   - Playfair → Columnar → DES
```

---

## Understanding the Output

### Text Encryption Response

```json
{
  "status": "success",
  "plaintext": "HELLO",
  "ciphertext": "5a1b2c3d...",           // Preview (truncated)
  "ciphertext_full": "5a1b2c3d4e5f6g7h", // Full hex string (download this)
  "size_increase": "2.34x"                // Hex encoding expands size
}
```

**Size increase explained:**
- Original: "HELLO" = 5 bytes
- After encryption & DES: 8 bytes (DES block)
- Hex encoded: 16 characters (1 byte = 2 hex chars)
- Result: 16 chars ÷ 5 bytes = **3.2x** increase

### File Operations

**Encryption produces:**
- File: `originalname.txt.encrypted`
- Format: Hex-encoded text (can view in any text editor)
- Size: ~2-3x larger than original

**Decryption produces:**
- File: `decrypted_originalname.txt.encrypted`
- Format: Original text format
- Size: Same as original

---

## Troubleshooting

### Problem: "Keys not initialized" Error

**Error Message:**
```
Error: Key file not found: ...\.keys.json
Run  `python -m backend.keys --init`  to generate system keys.
```

**Solution:**
```bash
python backend/keys.py --init
```

Or if that fails:
```bash
python -c "from backend.keys import generate_keys, save_keys; save_keys(generate_keys())"
```

### Problem: Port 8000 Already in Use

**Error Message:**
```
ERROR:    Uvicorn running on http://0.0.0.0:8000 failed to start
```

**Solution 1 - Change Port:**
Edit `app.py`, change last line:
```python
uvicorn.run(app, host="0.0.0.0", port=8001)  # Use 8001 instead
```

**Solution 2 - Kill Process Using Port 8000:**
```powershell
# Windows PowerShell
Get-Process -Name *python* | Stop-Process -Force
```

### Problem: Module Import Errors

**Error Message:**
```
ModuleNotFoundError: No module named 'fastapi'
```

**Solution:**
```bash
# Make sure virtual environment is activated
.venv\Scripts\activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Problem: Can't Access http://localhost:8000

**Check if server is running:**
- Look for output showing "Uvicorn running on..."
- If not, start with: `python app.py`

**Check if port is correct:**
```bash
# Windows: Check what's listening on 8000
netstat -ano | findstr :8000
```

### Problem: File Encryption Shows Wrong File Size

This is normal! The size increases because:
1. Text → Playfair (same size, substitution)
2. → Columnar (same size, transposition)
3. → DES (padded to 8-byte blocks)
4. → Hex encoded (2 hex chars per byte = 2x+ size)

Final size is typically **2-3x** larger.

---

## What You're Seeing

### The 3-Layer Pipeline in Action

When you encrypt "HELLO WORLD":

```
INPUT: "HELLO WORLD"

LAYER 1: Playfair (Substitution)
├─ Build 5×5 grid from key
├─ Convert to digraphs (HE-LL-OW-OR-LD)
├─ Apply substitution rules
└─ OUTPUT: "ABCDEFGHIJKLMN..." (uppercase letters)

LAYER 2: Columnar (Transposition)
├─ Read key to get column order
├─ Write plaintext row-by-row
├─ Read columns in key order
└─ OUTPUT: "XYZABCDEFGHIJKL..." (rearranged letters)

LAYER 3: DES (Block Cipher)
├─ Group into 8-byte blocks
├─ Apply DES encryption
└─ OUTPUT: Binary data

FORMAT: Hex Encoding
├─ Convert binary → hex string
└─ FINAL: "5a1b2c3d4e5f6g7h..." (can transmit/store safely)

DOWNLOAD: Encrypted file with hex content
```

### Decryption (Reverse Order)

```
INPUT: "5a1b2c3d4e5f6g7h..." (hex string)

LAYER 3: DES (Reverse)
└─ Hex → Binary → DES Decrypt

LAYER 2: Columnar (Reverse)
└─ Undo column reordering

LAYER 1: Playfair (Reverse)
└─ Undo substitution

OUTPUT: "HELLO WORLD" (original recovered!)
```

---

## Quick Commands Reference

```bash
# Activate virtual environment
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Generate keys (first time)
python backend/keys.py --init

# Start server
python app.py

# Run tests
pytest tests/ -v

# Check coverage
pytest tests/ --cov=backend --cov-report=html

# Stop server
Ctrl + C
```

---

## File Structure (What You Have)

```
d:\BCA\4th_sem\File_Encrypt\
├── app.py                      ← START HERE (FastAPI app)
├── backend/
│   ├── playfair.py            (Layer 1: Substitution)
│   ├── columnar.py            (Layer 2: Transposition)
│   ├── des_cipher.py          (Layer 3: Block cipher)
│   ├── pipeline.py            (Combines all 3 layers)
│   ├── keys.py                (Key generation)
│   └── file_io.py             (File operations)
├── frontend/
│   ├── templates/
│   │   └── index.html         (Web UI)
│   └── static/
│       ├── app.js             (JavaScript logic)
│       └── style.css          (Styling)
├── tests/                      (Test suite)
├── .keys.json                 (Auto-generated - git-ignored)
├── uploads/                   (Temp uploads)
├── outputs/                   (Encrypted files)
├── requirements.txt           (Dependencies)
├── pytest.ini                 (Test config)
└── README.md                  (Documentation)
```

---

## Next Steps After Starting

1. ✅ **Server is running** at http://localhost:8000
2. ✅ **Test web UI** - Try encrypt/decrypt text
3. ✅ **Test file ops** - Upload and encrypt a file
4. ✅ **View API docs** - Visit http://localhost:8000/docs
5. ✅ **Run tests** - `pytest tests/ -v`

---

## Getting Help

If something doesn't work:

1. **Check error message** - Usually tells you what's wrong
2. **Try the troubleshooting section** above
3. **Check TESTING.md** - If tests fail
4. **Read README.md** - For architecture overview
5. **Look at examples** - See `tests/examples.py` for code patterns

---

## Performance Tips

- **First encryption is slower** - DES initialization
- **Large files** - Encryption takes proportional time
- **Multiple requests** - Server handles them async in background
- **File size limit** - 10 MB by default (configurable in app.py)

---

## Security Notes

⚠️ **For Educational Use Only**
- Playfair: Vulnerable to frequency analysis
- Columnar: Breakable with large ciphertexts
- DES: 56-bit is too small for real security
- Use AES-256 for actual sensitive data

✅ **What This System IS Good For:**
- Learning how encryption works
- Understanding multi-layer pipelines
- Testing API development with FastAPI
- Understanding pytest and testing

---

## You're All Set! 🎉

Your complete encryption pipeline is ready to use:

✅ FastAPI backend with 5 endpoints
✅ Beautiful web UI for easy use
✅ Swagger documentation at /docs
✅ Comprehensive test suite (38 tests)
✅ 3-layer encryption (Playfair → Columnar → DES)
✅ File encryption/decryption
✅ Text encryption/decryption

**Start the server and visit http://localhost:8000 to see your work!**
