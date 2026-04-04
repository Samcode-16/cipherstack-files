"""
FastAPI web application for file encryption/decryption.
 
Provides REST API endpoints for:
  - POST /api/encrypt       - Upload file, encrypt, download
  - POST /api/decrypt       - Upload encrypted file, decrypt, download
  - POST /api/encrypt-text  - Encrypt text string
  - POST /api/decrypt-text  - Decrypt text string
  - GET  /api/status        - Check system status
  - GET  /                  - Serve index.html (frontend)
 
Binary files (pdf, doc, docx, png, jpg, jpeg):
  - Converted to base64 then encrypted with DES only (bypasses Playfair/Columnar
    which only handle letters and would mangle base64 characters).
  - Encrypted file starts with "BIN:" marker so decrypt knows which path to use.
 
Text files (txt, log, csv, json, md):
  - Run through the full 3-layer pipeline: Playfair → Columnar → DES.
"""
 
import base64
import os
import json
import io
from pathlib import Path
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from backend import pipeline, file_io
from backend.keys import load_keys
from backend.des_cipher import encrypt as des_encrypt, decrypt as des_decrypt
 
# ---------------------------------------------------------------------------
# FastAPI app configuration
# ---------------------------------------------------------------------------
 
app = FastAPI(
    title="File Encryption Pipeline",
    description="3-layer encryption system: Playfair → Columnar → DES",
    version="3.0"
)
 
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
 
# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
 
UPLOAD_FOLDER = Path("uploads")
OUTPUT_FOLDER = Path("outputs")
 
# Text files → full 3-layer pipeline
# Binary files → DES only (base64 encoded)
ALLOWED_EXTENSIONS = {'txt', 'log', 'csv', 'json', 'md', 'pdf', 'doc', 'docx', 'png', 'jpg', 'jpeg'}
BINARY_EXTENSIONS  = {'pdf', 'doc', 'docx', 'png', 'jpg', 'jpeg'}
 
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
 
UPLOAD_FOLDER.mkdir(exist_ok=True)
OUTPUT_FOLDER.mkdir(exist_ok=True)
 
STATIC_DIR = Path("frontend/static")
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
 
 
# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------
 
class TextEncryptRequest(BaseModel):
    text: str
 
class TextDecryptRequest(BaseModel):
    ciphertext: str
 
class StatusResponse(BaseModel):
    status: str
    pipeline: str
    keys_loaded: bool
    playfair_key_length: int
    columnar_key_length: int
    des_key_length: int
    max_file_size_mb: float
 
 
# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
 
def allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
 
 
def get_unique_filename(filepath: Path) -> Path:
    if not filepath.exists():
        return filepath
    stem, suffix, parent, counter = filepath.stem, filepath.suffix, filepath.parent, 1
    while True:
        new_path = parent / f"{stem}_{counter}{suffix}"
        if not new_path.exists():
            return new_path
        counter += 1
 
 
def _encrypt_binary(contents: bytes, des_key: str) -> str:
    """
    Encrypt raw binary bytes.
    1. Base64-encode the bytes → safe ASCII string
    2. Encrypt with DES
    3. Prepend "BIN:<8-hex-length>:" so decrypt knows the exact b64 length
       (DES PKCS7 padding can add extra chars that would break base64 decode)
    """
    b64 = base64.b64encode(contents).decode('utf-8')
    length_hex = f"{len(b64):08x}"          # 8 hex chars = up to 4 GB
    ciphertext = des_encrypt(b64, des_key)
    return f"BIN:{length_hex}:{ciphertext}"
 
 
def _decrypt_binary(file_content: str, des_key: str) -> bytes:
    """
    Reverse of _encrypt_binary.
    Format: BIN:<8-hex-length>:<DES-ciphertext>
    """
    # Strip the "BIN:" marker
    rest = file_content[4:]                  # "<8-hex-length>:<DES-ciphertext>"
    length_hex = rest[:8]                    # first 8 chars = original b64 length
    des_ciphertext = rest[9:]                # skip the colon at position 8
    original_b64_length = int(length_hex, 16)
 
    b64 = des_decrypt(des_ciphertext, des_key)
    b64 = b64[:original_b64_length]          # trim any DES padding chars
    return base64.b64decode(b64)
 
 
# ---------------------------------------------------------------------------
# Routes - Frontend
# ---------------------------------------------------------------------------
 
@app.get("/", response_class=HTMLResponse)
async def index():
    try:
        html = Path("frontend/templates/index.html").read_text(encoding='utf-8')
        html = html.replace("{{ url_for('static', filename='style.css') }}", "/static/style.css")
        html = html.replace("{{ url_for('static', filename='app.js') }}",   "/static/app.js")
        return html
    except Exception as e:
        return f"<h1>Error</h1><p>{e}</p>"
 
 
# ---------------------------------------------------------------------------
# Routes - Status
# ---------------------------------------------------------------------------
 
@app.get("/api/status", response_model=StatusResponse)
async def get_status():
    try:
        keys = load_keys()
        return StatusResponse(
            status="ready",
            pipeline="3-layer (Playfair → Columnar → DES)",
            keys_loaded=True,
            playfair_key_length=len(keys['playfair']),
            columnar_key_length=len(keys['columnar']),
            des_key_length=len(keys['des']),
            max_file_size_mb=MAX_FILE_SIZE / (1024 * 1024)
        )
    except FileNotFoundError:
        raise HTTPException(status_code=503,
            detail="Keys not initialized. Run: python -m backend.keys --init")
 
 
# ---------------------------------------------------------------------------
# Routes - /api/encrypt  and  /api/decrypt  (legacy streaming endpoints)
# ---------------------------------------------------------------------------
 
@app.post("/api/encrypt")
async def encrypt_file(file: UploadFile = File(...)):
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
        if not allowed_file(file.filename):
            raise HTTPException(status_code=400,
                detail=f"File type not allowed. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}")
 
        contents = await file.read()
        if len(contents) > MAX_FILE_SIZE:
            raise HTTPException(status_code=413,
                detail=f"File too large. Max: {MAX_FILE_SIZE/(1024*1024):.1f} MB")
 
        keys = load_keys()
        ext = Path(file.filename).suffix.lstrip('.').lower()
 
        if ext in BINARY_EXTENSIONS:
            ciphertext = _encrypt_binary(contents, keys['des'])
        else:
            try:
                plaintext = contents.decode('utf-8')
            except UnicodeDecodeError:
                plaintext = contents.decode('latin-1')
            ciphertext = pipeline.encrypt_text(plaintext)
 
        encrypted_filename = Path(file.filename).name + ".encrypted"
        return StreamingResponse(
            iter([ciphertext.encode('utf-8')]),
            media_type='application/octet-stream',
            headers={"Content-Disposition": f"attachment; filename={encrypted_filename}"}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Encryption failed: {str(e)}")
 
 
@app.post("/api/decrypt")
async def decrypt_file(file: UploadFile = File(...)):
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
 
        contents = await file.read()
        try:
            file_content = contents.decode('utf-8').strip()
        except UnicodeDecodeError:
            raise HTTPException(status_code=400, detail="File is corrupted or not a valid .encrypted file")
 
        keys = load_keys()
 
        if file_content.startswith("BIN:"):
            result_bytes = _decrypt_binary(file_content, keys['des'])
            decrypted_filename = file.filename.replace('.encrypted', '') or f"decrypted_{file.filename}"
            return StreamingResponse(
                iter([result_bytes]),
                media_type='application/octet-stream',
                headers={"Content-Disposition": f"attachment; filename={decrypted_filename}"}
            )
        else:
            plaintext = pipeline.decrypt_text(file_content)
            decrypted_filename = file.filename.replace('.encrypted', '') or f"decrypted_{file.filename}"
            return StreamingResponse(
                iter([plaintext.encode('utf-8')]),
                media_type='text/plain',
                headers={"Content-Disposition": f"attachment; filename={decrypted_filename}"}
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Decryption failed: {str(e)}")
 
 
# ---------------------------------------------------------------------------
# Routes - Text endpoints (for /docs testing)
# ---------------------------------------------------------------------------
 
@app.post("/api/encrypt-text")
async def encrypt_text_endpoint(request: TextEncryptRequest):
    try:
        if not request.text:
            raise HTTPException(status_code=400, detail="No text provided")
        ciphertext = pipeline.encrypt_text(request.text)
        return JSONResponse({
            "status": "success",
            "plaintext": request.text,
            "ciphertext": ciphertext[:100] + "..." if len(ciphertext) > 100 else ciphertext,
            "ciphertext_full": ciphertext,
            "size_increase": f"{len(ciphertext) / len(request.text):.2f}x"
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
 
 
@app.post("/api/decrypt-text")
async def decrypt_text_endpoint(request: TextDecryptRequest):
    try:
        if not request.ciphertext:
            raise HTTPException(status_code=400, detail="No ciphertext provided")
        plaintext = pipeline.decrypt_text(request.ciphertext)
        return JSONResponse({
            "status": "success",
            "ciphertext": request.ciphertext[:100] + "..." if len(request.ciphertext) > 100 else request.ciphertext,
            "plaintext": plaintext
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
 
 
# ---------------------------------------------------------------------------
# Routes - /process  (main UI endpoint)
# ---------------------------------------------------------------------------
 
@app.post("/process")
async def process_file(
    file: UploadFile = File(...),
    mode: str = "encrypt"
):
    try:
        if not file.filename:
            return JSONResponse(status_code=400,
                content={"success": False, "error": "No file provided"})
 
        if mode not in ["encrypt", "decrypt"]:
            return JSONResponse(status_code=400,
                content={"success": False, "error": "Mode must be 'encrypt' or 'decrypt'"})
 
        contents = await file.read()
        if len(contents) > MAX_FILE_SIZE:
            return JSONResponse(status_code=413,
                content={"success": False, "error": f"File too large (max {MAX_FILE_SIZE/(1024*1024):.0f} MB)"})
 
        keys = load_keys()
 
        # ── ENCRYPT ──────────────────────────────────────────────────────────
        if mode == "encrypt":
            ext = Path(file.filename).suffix.lstrip('.').lower()
 
            if ext in BINARY_EXTENSIONS:
                # Binary path: base64 → DES only (Playfair/Columnar cannot
                # handle base64 characters like +, /, = without corruption)
                result = _encrypt_binary(contents, keys['des'])
            else:
                # Text path: full 3-layer pipeline
                try:
                    file_content = contents.decode('utf-8')
                except UnicodeDecodeError:
                    file_content = contents.decode('latin-1')
                result = pipeline.encrypt_text(file_content)
 
            output_filename = Path(file.filename).name + ".encrypted"
            output_path = get_unique_filename(OUTPUT_FOLDER / output_filename)
            output_path.write_text(result, encoding='utf-8')
 
        # ── DECRYPT ──────────────────────────────────────────────────────────
        else:
            try:
                file_content = contents.decode('utf-8').strip()
            except UnicodeDecodeError:
                return JSONResponse(status_code=400,
                    content={"success": False,
                             "error": "File is corrupted or not a valid .encrypted file"})
 
            if not file_content:
                return JSONResponse(status_code=400,
                    content={"success": False, "error": "File is empty"})
 
            # Reconstruct original filename
            fname = file.filename
            output_filename = fname[:-len('.encrypted')] if fname.endswith('.encrypted') \
                              else f"decrypted_{fname}"
            output_path = get_unique_filename(OUTPUT_FOLDER / output_filename)
 
            if file_content.startswith("BIN:"):
                # Binary path: DES decrypt → base64 decode → original bytes
                try:
                    binary_data = _decrypt_binary(file_content, keys['des'])
                except Exception as e:
                    return JSONResponse(status_code=500,
                        content={"success": False,
                                 "error": f"Binary decryption failed: {str(e)}"})
                output_path.write_bytes(binary_data)
 
            else:
                # Text path: validate hex format then full pipeline decrypt
                if len(file_content) < 10:
                    return JSONResponse(status_code=400,
                        content={"success": False,
                                 "error": "File is too short to be a valid encrypted file"})
 
                # Quick sanity check — first 8 chars must be hex
                if not all(c in '0123456789abcdefABCDEF' for c in file_content[:8]):
                    return JSONResponse(status_code=400,
                        content={"success": False,
                                 "error": "This file was not encrypted by this system, or is corrupted"})
 
                try:
                    result = pipeline.decrypt_text(file_content)
                except Exception as e:
                    return JSONResponse(status_code=500,
                        content={"success": False,
                                 "error": f"Decryption failed: {str(e)}"})
                output_path.write_text(result, encoding='utf-8')
 
        return JSONResponse({"success": True, "filename": output_path.name})
 
    except Exception as e:
        return JSONResponse(status_code=500,
            content={"success": False, "error": f"Processing failed: {str(e)}"})
 
 
# ---------------------------------------------------------------------------
# Routes - Download
# ---------------------------------------------------------------------------
 
@app.get("/download/{filename}")
async def download_file(filename: str):
    try:
        filename  = Path(filename).name   # prevent path traversal
        file_path = OUTPUT_FOLDER / filename
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        return FileResponse(path=file_path, filename=filename,
                            media_type='application/octet-stream')
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")
 
 
# ---------------------------------------------------------------------------
# Exception handlers
# ---------------------------------------------------------------------------
 
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})
 
@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    return JSONResponse(status_code=500, content={"error": "Internal server error"})
 
 
# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
 
if __name__ == "__main__":
    import uvicorn
    try:
        keys = load_keys()
        print("[app] Keys loaded successfully")
        print("[app] Starting FastAPI server on http://localhost:8000")
        print("[app] API docs: http://localhost:8000/docs")
        uvicorn.run(app, host="0.0.0.0", port=8000)
    except FileNotFoundError as e:
        print(f"[app] Error: {e}")
        print("[app] Initialize keys first: python -m backend.keys --init")