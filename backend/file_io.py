"""
File I/O utilities for encryption pipeline.

Handles reading/writing encrypted files with proper error handling, logging,
and metadata tracking.
"""

import json
from pathlib import Path
from datetime import datetime
from backend import pipeline


# ---------------------------------------------------------------------------
# File operations with metadata
# ---------------------------------------------------------------------------

def create_metadata(original_filename: str, action: str, file_size: int) -> dict:
    """
    Create metadata dictionary for encrypted file.
    
    Args:
        original_filename: Name of the original file
        action: "encrypt" or "decrypt"
        file_size: Size of file before operation
    
    Returns:
        Metadata dictionary
    """
    return {
        "timestamp": datetime.now().isoformat(),
        "action": action,
        "original_filename": original_filename,
        "file_size": file_size,
        "version": "3.0"  # 3-layer pipeline
    }


def encrypt_file_with_metadata(input_path: str, output_dir: str = "outputs") -> dict:
    """
    Encrypt a file and save with metadata JSON.
    
    Args:
        input_path: Path to plaintext file
        output_dir: Directory to save encrypted file and metadata
    
    Returns:
        Result dictionary:
        {
            "status": "success" | "error",
            "input_file": str,
            "output_file": str,
            "metadata_file": str,
            "original_size": int,
            "encrypted_size": int,
            "message": str
        }
    """
    try:
        input_file = Path(input_path)
        if not input_file.exists():
            return {
                "status": "error",
                "message": f"File not found: {input_path}"
            }
        
        # Read plaintext
        plaintext = input_file.read_text(encoding='utf-8')
        original_size = len(plaintext.encode('utf-8'))
        
        # Encrypt
        ciphertext = pipeline.encrypt_text(plaintext)
        
        # Prepare output paths
        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)
        
        encrypted_filename = f"{input_file.stem}.encrypted"
        metadata_filename = f"{input_file.stem}.metadata.json"
        
        encrypted_path = output_dir_path / encrypted_filename
        metadata_path = output_dir_path / metadata_filename
        
        # Write encrypted file
        encrypted_path.write_text(ciphertext, encoding='utf-8')
        encrypted_size = len(ciphertext.encode('utf-8'))
        
        # Write metadata
        metadata = create_metadata(
            original_filename=input_file.name,
            action="encrypt",
            file_size=original_size
        )
        metadata_path.write_text(json.dumps(metadata, indent=2), encoding='utf-8')
        
        return {
            "status": "success",
            "input_file": str(input_file),
            "output_file": str(encrypted_path),
            "metadata_file": str(metadata_path),
            "original_size": original_size,
            "encrypted_size": encrypted_size,
            "message": f"Successfully encrypted: {input_file.name}"
        }
    
    except Exception as e:
        return {
            "status": "error",
            "message": f"Encryption failed: {str(e)}"
        }


def decrypt_file_with_metadata(
    encrypted_path: str,
    metadata_path: str = None,
    output_dir: str = "outputs"
) -> dict:
    """
    Decrypt a file using optional metadata for original filename.
    
    Args:
        encrypted_path: Path to encrypted file
        metadata_path: Optional path to metadata JSON (auto-detected if None)
        output_dir: Directory to save decrypted file
    
    Returns:
        Result dictionary with decryption status
    """
    try:
        enc_file = Path(encrypted_path)
        if not enc_file.exists():
            return {
                "status": "error",
                "message": f"File not found: {encrypted_path}"
            }
        
        # Try to find metadata if not provided
        if metadata_path is None:
            metadata_path = enc_file.parent / f"{enc_file.stem.replace('.encrypted', '')}.metadata.json"
        
        # Load metadata if available
        original_filename = enc_file.stem.replace('.encrypted', '')
        if Path(metadata_path).exists():
            metadata = json.loads(Path(metadata_path).read_text())
            original_filename = metadata.get("original_filename", original_filename)
        
        # Read encrypted file
        ciphertext = enc_file.read_text(encoding='utf-8')
        encrypted_size = len(ciphertext.encode('utf-8'))
        
        # Decrypt
        plaintext = pipeline.decrypt_text(ciphertext)
        
        # Write decrypted file
        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)
        
        decrypted_path = output_dir_path / original_filename
        decrypted_path.write_text(plaintext, encoding='utf-8')
        
        return {
            "status": "success",
            "input_file": str(enc_file),
            "output_file": str(decrypted_path),
            "original_filename": original_filename,
            "encrypted_size": encrypted_size,
            "decrypted_size": len(plaintext.encode('utf-8')),
            "message": f"Successfully decrypted: {original_filename}"
        }
    
    except Exception as e:
        return {
            "status": "error",
            "message": f"Decryption failed: {str(e)}"
        }


def batch_encrypt_directory(directory: str, output_dir: str = "outputs") -> list:
    """
    Encrypt all text files in a directory.
    
    Args:
        directory: Directory containing files to encrypt
        output_dir: Output directory for encrypted files
    
    Returns:
        List of result dictionaries (one per file)
    """
    results = []
    dir_path = Path(directory)
    
    if not dir_path.exists():
        return [{"status": "error", "message": f"Directory not found: {directory}"}]
    
    # Find all text files
    for file_path in dir_path.glob("*.txt"):
        result = encrypt_file_with_metadata(str(file_path), output_dir)
        results.append(result)
    
    return results


# ---------------------------------------------------------------------------
# Quick smoke-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Test with a simple text file
    test_file = Path("test_input.txt")
    test_file.write_text("HELLO WORLD FROM FILE")
    
    print("Testing encrypt_file_with_metadata...")
    result = encrypt_file_with_metadata(str(test_file), "outputs")
    print(json.dumps(result, indent=2))
    
    print("\nTesting decrypt_file_with_metadata...")
    if result["status"] == "success":
        decrypt_result = decrypt_file_with_metadata(result["output_file"], output_dir="outputs_decrypted")
        print(json.dumps(decrypt_result, indent=2))
    
    # Cleanup
    test_file.unlink()
