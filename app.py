"""
FastAPI web application for file encryption/decryption.

Provides REST API endpoints for:
  - POST /api/encrypt   – Upload file, encrypt, download
  - POST /api/decrypt   – Upload encrypted file, decrypt, download
  - POST /api/encrypt-text  – Encrypt text string
  - POST /api/decrypt-text  – Decrypt text string
  - GET  /api/status    – Check system status
  - GET  /              – Serve index.html (frontend)
"""

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

# ---------------------------------------------------------------------------
# FastAPI app configuration
# ---------------------------------------------------------------------------

app = FastAPI(
    title="File Encryption Pipeline",
    description="3-layer encryption system: Playfair → Columnar → DES",
    version="3.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
UPLOAD_FOLDER = Path("uploads")
OUTPUT_FOLDER = Path("outputs")
ALLOWED_EXTENSIONS = {'txt', 'log', 'csv', 'json', 'md'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

# Create folders if they don't exist
UPLOAD_FOLDER.mkdir(exist_ok=True)
OUTPUT_FOLDER.mkdir(exist_ok=True)

# Mount static files
STATIC_DIR = Path("frontend/static")
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# ---------------------------------------------------------------------------
# Pydantic Models
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
# Helper functions
# ---------------------------------------------------------------------------

def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_unique_filename(filepath: Path) -> Path:
    """Generate unique filename if it already exists."""
    if not filepath.exists():
        return filepath
    
    stem = filepath.stem
    suffix = filepath.suffix
    parent = filepath.parent
    counter = 1
    
    while True:
        new_name = f"{stem}_{counter}{suffix}"
        new_path = parent / new_name
        if not new_path.exists():
            return new_path
        counter += 1


# ---------------------------------------------------------------------------
# Routes - Frontend
# ---------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def index():
    """Serve the main HTML page."""
    try:
        html_file = Path("frontend/templates/index.html")
        html_content = html_file.read_text(encoding='utf-8')
        # Replace Flask/Jinja2 template syntax with direct paths
        html_content = html_content.replace("{{ url_for('static', filename='style.css') }}", "/static/style.css")
        html_content = html_content.replace("{{ url_for('static', filename='app.js') }}", "/static/app.js")
        return html_content
    except Exception as e:
        return f"<h1>Error</h1><p>{str(e)}</p>"


# ---------------------------------------------------------------------------
# Routes - API Status
# ---------------------------------------------------------------------------

@app.get("/api/status", response_model=StatusResponse)
async def get_status():
    """Check system status and pipeline readiness."""
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
        raise HTTPException(
            status_code=503,
            detail="Keys not initialized. Run: python -m backend.keys --init"
        )


# ---------------------------------------------------------------------------
# Routes - File Operations
# ---------------------------------------------------------------------------

@app.post("/api/encrypt")
async def encrypt_file(file: UploadFile = File(...)):
    """
    Endpoint to encrypt a file.
    
    Args:
        file: Uploaded file
    
    Returns:
        Encrypted file for download, or error JSON
    
    Allowed types: .txt, .log, .csv, .json, .md
    """
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
        
        if not allowed_file(file.filename):
            raise HTTPException(
                status_code=400,
                detail=f"File type not allowed. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
            )
        
        # Check file size
        contents = await file.read()
        if len(contents) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size: {MAX_FILE_SIZE / (1024*1024):.1f} MB"
            )
        
        # Decrypt content
        plaintext = contents.decode('utf-8')
        
        # Encrypt
        ciphertext = pipeline.encrypt_text(plaintext)
        
        # Return encrypted file using StreamingResponse
        encrypted_filename = f"{Path(file.filename).stem}.encrypted"
        
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
    """
    Endpoint to decrypt a file.
    
    Args:
        file: Uploaded encrypted file
    
    Returns:
        Decrypted file for download, or error JSON
    """
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
        
        # Read file
        contents = await file.read()
        ciphertext = contents.decode('utf-8')
        
        # Decrypt
        plaintext = pipeline.decrypt_text(ciphertext)
        
        # Return decrypted file using StreamingResponse
        decrypted_filename = file.filename.replace('.encrypted', '')
        if decrypted_filename == file.filename:
            decrypted_filename = f"decrypted_{file.filename}"
        
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
# Routes - Text Operations (Testing)
# ---------------------------------------------------------------------------

@app.post("/api/encrypt-text")
async def encrypt_text_endpoint(request: TextEncryptRequest):
    """
    Encrypt a text string (useful for testing).
    
    Request body:
        {
            "text": "HELLO WORLD"
        }
    """
    try:
        if not request.text:
            raise HTTPException(status_code=400, detail="No text provided")
        
        plaintext = request.text
        ciphertext = pipeline.encrypt_text(plaintext)
        
        return JSONResponse({
            "status": "success",
            "plaintext": plaintext,
            "ciphertext": ciphertext[:100] + "..." if len(ciphertext) > 100 else ciphertext,
            "ciphertext_full": ciphertext,
            "size_increase": f"{len(ciphertext) / len(plaintext):.2f}x"
        })
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/decrypt-text")
async def decrypt_text_endpoint(request: TextDecryptRequest):
    """
    Decrypt a hex-encoded ciphertext.
    
    Request body:
        {
            "ciphertext": "hex-encoded-input..."
        }
    """
    try:
        if not request.ciphertext:
            raise HTTPException(status_code=400, detail="No ciphertext provided")
        
        ciphertext = request.ciphertext
        plaintext = pipeline.decrypt_text(ciphertext)
        
        return JSONResponse({
            "status": "success",
            "ciphertext": ciphertext[:100] + "..." if len(ciphertext) > 100 else ciphertext,
            "plaintext": plaintext
        })
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# Routes - Unified Process Endpoint (for professional UI)
# ---------------------------------------------------------------------------

@app.post("/process")
async def process_file(
    file: UploadFile = File(...),
    mode: str = "encrypt"
):
    """
    Unified endpoint for the professional UI.
    Uses system-generated keys for secure encryption/decryption.
    
    Args:
        file: Uploaded file
        mode: 'encrypt' or 'decrypt'
    
    Returns:
        JSON with {success: true, filename: "..."} or {success: false, error: "..."}
    """
    try:
        # Validate inputs
        if not file.filename:
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": "No file provided"}
            )
        
        if mode not in ["encrypt", "decrypt"]:
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": "Mode must be 'encrypt' or 'decrypt'"}
            )
        
        # Read file contents
        contents = await file.read()
        if len(contents) > MAX_FILE_SIZE:
            return JSONResponse(
                status_code=413,
                content={"success": False, "error": f"File too large (max {MAX_FILE_SIZE / (1024*1024):.0f} MB)"}
            )
        
        # Decode file content
        try:
            file_content = contents.decode('utf-8')
        except UnicodeDecodeError:
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": "File must be text-based (UTF-8)"}
            )
        
        # Process file
        if mode == "encrypt":
            result = pipeline.encrypt_text(file_content)
            base_name = Path(file.filename).stem
            output_filename = f"{base_name}.encrypted"
        else:  # decrypt
            result = pipeline.decrypt_text(file_content)
            # Remove .encrypted extension if present
            if file.filename.endswith('.encrypted'):
                output_filename = file.filename[:-10]
            else:
                output_filename = f"decrypted_{file.filename}"
        
        # Save result to outputs folder
        output_path = OUTPUT_FOLDER / output_filename
        output_path = get_unique_filename(output_path)
        output_path.write_text(result, encoding='utf-8')
        
        return JSONResponse({
            "success": True,
            "filename": output_filename
        })
    
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": f"Processing failed: {str(e)}"}
        )


# ---------------------------------------------------------------------------
# Routes - File Download
# ---------------------------------------------------------------------------

@app.get("/download/{filename}")
async def download_file(filename: str):
    """
    Download a processed file from the outputs folder.
    
    Args:
        filename: Name of the file to download
    """
    try:
        # Security: sanitize filename
        filename = Path(filename).name  # Only allow filename, no path traversal
        file_path = OUTPUT_FOLDER / filename
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        # Return file for download
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type='application/octet-stream'
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")


# ---------------------------------------------------------------------------
# Exception handlers
# ---------------------------------------------------------------------------

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle unexpected exceptions."""
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"},
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    
    try:
        # Verify keys are loaded
        keys = load_keys()
        print("[app] ✓ Keys loaded successfully")
        print("[app] Starting FastAPI server on http://localhost:8000")
        print("[app] API docs available at http://localhost:8000/docs")
        print("[app] Alternative docs at http://localhost:8000/redoc")
        
        uvicorn.run(app, host="0.0.0.0", port=8000)
    
    except FileNotFoundError as e:
        print(f"[app] Error: {e}")
        print("[app] Initialize keys first: python -m backend.keys --init")

