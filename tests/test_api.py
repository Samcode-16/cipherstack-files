"""
FastAPI Testing Guide - Comprehensive examples for testing the encryption pipeline

FastAPI provides excellent testing features:
1. TestClient - Synchronous HTTP client for testing
2. pytest integration - Standard Python testing framework
3. Dependency overriding - Mock dependencies easily
4. Fixtures - Reusable test setup
5. Async support - Test async endpoints

Usage:
------
    pip install pytest pytest-asyncio httpx

    # Run all tests
    pytest tests/

    # Run with verbose output
    pytest tests/ -v

    # Run specific test file
    pytest tests/test_api.py

    # Run with coverage
    pytest tests/ --cov=backend --cov-report=html
"""

import pytest
import json
import io
from pathlib import Path
from fastapi.testclient import TestClient
from backend import pipeline, file_io, playfair, columnar, des_cipher
from backend.keys import load_keys, generate_keys, save_keys

# Import the FastAPI app
from app import app, ALLOWED_EXTENSIONS, MAX_FILE_SIZE


# ============================================================================
# Test Client Setup
# ============================================================================

@pytest.fixture
def client():
    """
    Create a test client for the FastAPI app.
    
    This fixture provides an HTTP client that can make requests to the app
    without running a server.
    """
    return TestClient(app)


@pytest.fixture
def test_plaintext():
    """Sample plaintext for encryption testing."""
    return "HELLO WORLD ENCRYPTION TEST"


@pytest.fixture
def test_file():
    """Create a temporary test file."""
    temp_file = Path("test_temp.txt")
    temp_file.write_text("This is a test file for encryption.")
    yield temp_file
    # Cleanup
    if temp_file.exists():
        temp_file.unlink()


# ============================================================================
# Status Endpoint Tests
# ============================================================================

class TestStatusEndpoint:
    """Test the /api/status endpoint."""
    
    def test_status_returns_200(self, client):
        """Status endpoint should return 200 OK."""
        response = client.get("/api/status")
        assert response.status_code == 200
    
    def test_status_returns_ready(self, client):
        """Status should indicate system is ready."""
        response = client.get("/api/status")
        data = response.json()
        assert data["status"] == "ready"
        assert data["keys_loaded"] is True
    
    def test_status_has_required_fields(self, client):
        """Status response should have all required fields."""
        response = client.get("/api/status")
        data = response.json()
        
        required_fields = [
            "status",
            "pipeline",
            "keys_loaded",
            "playfair_key_length",
            "columnar_key_length",
            "des_key_length",
            "max_file_size_mb"
        ]
        
        for field in required_fields:
            assert field in data, f"Missing field: {field}"
    
    def test_status_pipeline_description(self, client):
        """Pipeline description should be correct."""
        response = client.get("/api/status")
        data = response.json()
        assert "Playfair" in data["pipeline"]
        assert "Columnar" in data["pipeline"]
        assert "DES" in data["pipeline"]
    
    def test_status_key_lengths(self, client):
        """Key lengths should match expected values."""
        response = client.get("/api/status")
        data = response.json()
        
        # Expected lengths from backend.keys
        assert data["playfair_key_length"] >= 6
        assert data["columnar_key_length"] >= 5
        assert data["des_key_length"] == 16  # 8 bytes as hex


# ============================================================================
# Text Encryption Tests
# ============================================================================

class TestTextEncryption:
    """Test text encryption/decryption endpoints."""
    
    def test_encrypt_text_returns_200(self, client, test_plaintext):
        """Encrypt text endpoint should return 200."""
        response = client.post(
            "/api/encrypt-text",
            json={"text": test_plaintext}
        )
        assert response.status_code == 200
    
    def test_encrypt_text_returns_ciphertext(self, client, test_plaintext):
        """Encrypted text should be returned."""
        response = client.post(
            "/api/encrypt-text",
            json={"text": test_plaintext}
        )
        data = response.json()
        
        assert "ciphertext_full" in data
        assert len(data["ciphertext_full"]) > 0
        assert data["plaintext"] == test_plaintext
    
    def test_encrypt_text_returns_hex(self, client, test_plaintext):
        """Ciphertext should be valid hex string."""
        response = client.post(
            "/api/encrypt-text",
            json={"text": test_plaintext}
        )
        data = response.json()
        ciphertext = data["ciphertext_full"]
        
        # Should be valid hex
        try:
            bytes.fromhex(ciphertext)
        except ValueError:
            assert False, "Ciphertext is not valid hex"
    
    def test_encrypt_text_no_plaintext_returns_400(self, client):
        """Should return 400 if no text provided."""
        response = client.post(
            "/api/encrypt-text",
            json={"text": ""}
        )
        assert response.status_code == 400
    
    def test_encrypt_text_shows_size_increase(self, client, test_plaintext):
        """Should show size increase in response."""
        response = client.post(
            "/api/encrypt-text",
            json={"text": test_plaintext}
        )
        data = response.json()
        
        assert "size_increase" in data
        # DES + hex encoding increases size significantly
        assert float(data["size_increase"].rstrip("x")) > 1.0
    
    def test_decrypt_text_reverses_encryption(self, client, test_plaintext):
        """Decrypted text should match original."""
        # Encrypt
        encrypt_response = client.post(
            "/api/encrypt-text",
            json={"text": test_plaintext}
        )
        ciphertext = encrypt_response.json()["ciphertext_full"]
        
        # Decrypt
        decrypt_response = client.post(
            "/api/decrypt-text",
            json={"ciphertext": ciphertext}
        )
        decrypted = decrypt_response.json()["plaintext"]
        
        # Playfair converts to uppercase and may have X padding in different positions
        # Compare by removing all X's and normalizing to uppercase
        assert decrypted.replace('X', '') == test_plaintext.upper().replace('X', '')
    
    def test_decrypt_text_no_ciphertext_returns_400(self, client):
        """Should return 400 if no ciphertext provided."""
        response = client.post(
            "/api/decrypt-text",
            json={"ciphertext": ""}
        )
        assert response.status_code == 400
    
    def test_decrypt_text_invalid_hex_returns_500(self, client):
        """Should return 500 if ciphertext is invalid hex."""
        response = client.post(
            "/api/decrypt-text",
            json={"ciphertext": "not_valid_hex_xyz"}
        )
        assert response.status_code == 500


# ============================================================================
# File Upload Tests
# ============================================================================

class TestFileEncryption:
    """Test file encryption endpoint."""
    
    def test_encrypt_file_returns_200(self, client, test_file):
        """Should return 200 for valid file upload."""
        with open(test_file, "rb") as f:
            response = client.post(
                "/api/encrypt",
                files={"file": f}
            )
        assert response.status_code == 200
    
    def test_encrypt_file_returns_encrypted_file(self, client, test_file):
        """Should return encrypted file in response."""
        with open(test_file, "rb") as f:
            response = client.post(
                "/api/encrypt",
                files={"file": f}
            )
        
        # Response should be binary data
        assert len(response.content) > 0
        
        # Response should include filename in headers
        assert "attachment" in response.headers.get("content-disposition", "")
    
    def test_encrypt_file_has_encrypted_extension(self, client, test_file):
        """Downloaded file should have .encrypted extension."""
        with open(test_file, "rb") as f:
            response = client.post(
                "/api/encrypt",
                files={"file": f}
            )
        
        disposition = response.headers.get("content-disposition", "")
        assert "encrypted" in disposition
    
    def test_encrypt_file_no_file_returns_400(self, client):
        """Should return 400 if no file provided."""
        response = client.post("/api/encrypt")
        assert response.status_code == 400
    
    def test_encrypt_file_wrong_extension_returns_400(self, client):
        """Should return 400 for unsupported file type."""
        file_content = io.BytesIO(b"test content")
        
        response = client.post(
            "/api/encrypt",
            files={"file": ("test.exe", file_content, "application/octet-stream")}
        )
        assert response.status_code == 400
        assert "not allowed" in response.json()["detail"].lower()
    
    def test_encrypt_file_allowed_extensions(self, client):
        """Should accept all allowed file extensions."""
        for ext in ALLOWED_EXTENSIONS:
            file_content = io.BytesIO(b"test content")
            
            response = client.post(
                "/api/encrypt",
                files={"file": (f"test.{ext}", file_content, "text/plain")}
            )
            
            # Should succeed (200) or fail with file size (not 400 for extension)
            assert response.status_code in [200, 413, 500]
    
    def test_encrypt_file_too_large_returns_413(self, client):
        """Should return 413 if file is too large."""
        # Create a file larger than MAX_FILE_SIZE
        large_content = b"x" * (MAX_FILE_SIZE + 1000)
        file_obj = io.BytesIO(large_content)
        
        response = client.post(
            "/api/encrypt",
            files={"file": ("large_file.txt", file_obj, "text/plain")}
        )
        assert response.status_code == 413


class TestFileDecryption:
    """Test file decryption endpoint."""
    
    def test_decrypt_file_returns_200(self, client, test_file):
        """Should return 200 for valid encrypted file."""
        # First encrypt a file
        with open(test_file, "rb") as f:
            encrypt_response = client.post(
                "/api/encrypt",
                files={"file": f}
            )
        
        # Then decrypt it
        encrypted_file = io.BytesIO(encrypt_response.content)
        decrypt_response = client.post(
            "/api/decrypt",
            files={"file": ("test.txt.encrypted", encrypted_file, "application/octet-stream")}
        )
        
        assert decrypt_response.status_code == 200
    
    def test_decrypt_file_recovers_original(self, client, test_file):
        """Decrypted file should match original (after normalization for cipher)."""
        # Read original
        original_content = test_file.read_text()
        
        # Encrypt
        with open(test_file, "rb") as f:
            encrypt_response = client.post(
                "/api/encrypt",
                files={"file": f}
            )
        
        # Decrypt
        encrypted_file = io.BytesIO(encrypt_response.content)
        decrypt_response = client.post(
            "/api/decrypt",
            files={"file": ("test.txt.encrypted", encrypted_file, "application/octet-stream")}
        )
        
        decrypted_content = decrypt_response.content.decode("utf-8")
        # Cipher converts to uppercase, removes spaces, may add X padding
        clean_decrypted = decrypted_content.replace('X', '').replace(' ', '')
        clean_original = original_content.upper().replace('X', '').replace(' ', '')
        assert clean_decrypted == clean_original
    
    def test_decrypt_file_no_file_returns_400(self, client):
        """Should return 400 if no file provided."""
        response = client.post("/api/decrypt")
        assert response.status_code == 400
    
    def test_decrypt_file_invalid_content_returns_500(self, client):
        """Should return 500 for invalid encrypted data."""
        invalid_file = io.BytesIO(b"not valid encrypted data")
        
        response = client.post(
            "/api/decrypt",
            files={"file": ("invalid.encrypted", invalid_file, "application/octet-stream")}
        )
        assert response.status_code == 500


# ============================================================================
# Integration Tests
# ============================================================================

class TestFullEncryptionPipeline:
    """Test the complete encryption/decryption pipeline."""
    
    def test_round_trip_text(self, client):
        """Encrypt and decrypt should recover original text."""
        messages = [
            "HELLO",
            "SECRET MESSAGE",
            "THE QUICK BROWN FOX JUMPS OVER THE LAZY DOG"
        ]
        
        for message in messages:
            # Encrypt
            encrypt_resp = client.post(
                "/api/encrypt-text",
                json={"text": message}
            )
            ciphertext = encrypt_resp.json()["ciphertext_full"]
            
            # Decrypt
            decrypt_resp = client.post(
                "/api/decrypt-text",
                json={"ciphertext": ciphertext}
            )
            decrypted = decrypt_resp.json()["plaintext"]
            
            # Playfair converts to uppercase, removes spaces, may have X padding
            clean_decrypted = decrypted.replace('X', '')
            clean_message = message.upper().replace(' ', '').replace('X', '')
            assert clean_decrypted == clean_message, f"Failed for message: {message}"
    
    def test_round_trip_file(self, client, test_file):
        """Encrypt and decrypt file should recover original."""
        original_content = test_file.read_text()
        
        # Encrypt
        with open(test_file, "rb") as f:
            encrypt_resp = client.post(
                "/api/encrypt",
                files={"file": f}
            )
        
        # Decrypt
        encrypt_resp.content  # File content
        encrypted_file = io.BytesIO(encrypt_resp.content)
        decrypt_resp = client.post(
            "/api/decrypt",
            files={"file": ("test.txt.encrypted", encrypted_file, "application/octet-stream")}
        )
        
        decrypted_content = decrypt_resp.content.decode("utf-8")
        assert decrypted_content == original_content
    
    def test_different_plaintexts_produce_different_ciphertexts(self, client):
        """Different messages should produce different ciphertexts."""
        resp1 = client.post(
            "/api/encrypt-text",
            json={"text": "MESSAGE A"}
        )
        resp2 = client.post(
            "/api/encrypt-text",
            json={"text": "MESSAGE B"}
        )
        
        cipher1 = resp1.json()["ciphertext_full"]
        cipher2 = resp2.json()["ciphertext_full"]
        
        assert cipher1 != cipher2
    
    def test_same_plaintext_produces_same_ciphertext(self, client):
        """Same message should always produce same ciphertext."""
        message = "CONSISTENT MESSAGE"
        
        resp1 = client.post(
            "/api/encrypt-text",
            json={"text": message}
        )
        resp2 = client.post(
            "/api/encrypt-text",
            json={"text": message}
        )
        
        cipher1 = resp1.json()["ciphertext_full"]
        cipher2 = resp2.json()["ciphertext_full"]
        
        assert cipher1 == cipher2


# ============================================================================
# Error Handling Tests
# ============================================================================

class TestErrorHandling:
    """Test error handling in API endpoints."""
    
    def test_invalid_json_returns_422(self, client):
        """Should return 422 for invalid JSON."""
        response = client.post(
            "/api/encrypt-text",
            json={"invalid_field": "value"}
        )
        assert response.status_code == 422
    
    def test_missing_required_field_returns_422(self, client):
        """Should return 422 for missing required fields."""
        response = client.post(
            "/api/encrypt-text",
            json={}
        )
        assert response.status_code == 422


# ============================================================================
# Performance Tests
# ============================================================================

class TestPerformance:
    """Test performance characteristics."""
    
    def test_encrypt_text_response_time(self, client, test_plaintext):
        """Encryption should complete reasonably fast."""
        import time
        
        start = time.time()
        response = client.post(
            "/api/encrypt-text",
            json={"text": test_plaintext}
        )
        elapsed = time.time() - start
        
        assert response.status_code == 200
        assert elapsed < 5.0  # Should complete in under 5 seconds
    
    def test_decrypt_text_response_time(self, client, test_plaintext):
        """Decryption should complete reasonably fast."""
        import time
        
        # Encrypt first
        encrypt_resp = client.post(
            "/api/encrypt-text",
            json={"text": test_plaintext}
        )
        ciphertext = encrypt_resp.json()["ciphertext_full"]
        
        # Time decryption
        start = time.time()
        response = client.post(
            "/api/decrypt-text",
            json={"ciphertext": ciphertext}
        )
        elapsed = time.time() - start
        
        assert response.status_code == 200
        assert elapsed < 5.0


# ============================================================================
# Backend Module Tests (Unit Tests)
# ============================================================================

class TestPlayfairCipher:
    """Test Playfair cipher directly."""
    
    def test_playfair_encrypt_decrypt_round_trip(self):
        """Playfair should recover plaintext after decryption."""
        key = "MONARCHY"
        plaintext = "INSTRUMENTS"
        
        ciphertext = playfair.encrypt(plaintext, key)
        decrypted = playfair.decrypt(ciphertext, key)
        
        # Playfair keeps X padding added during encryption, so strip and compare
        assert decrypted.rstrip('X') == plaintext
    
    def test_playfair_handles_duplicates(self):
        """Should handle duplicate letters with X padding."""
        key = "SECRET"
        plaintext = "BALLOON"  # Double L
        
        ciphertext = playfair.encrypt(plaintext, key)
        decrypted = playfair.decrypt(ciphertext, key)
        
        # Playfair inserts X for duplicates
        assert "X" in decrypted


class TestColumnarCipher:
    """Test Columnar transposition cipher directly."""
    
    def test_columnar_encrypt_decrypt_round_trip(self):
        """Columnar should recover plaintext after decryption."""
        key = "SECRET"
        plaintext = "HELLOWORLD"
        
        ciphertext = columnar.encrypt(plaintext, key)
        decrypted = columnar.decrypt(ciphertext, key)
        
        # Columnar pads with X to reach key length multiple, so strip padding
        # The padding added is: (key_len - (plaintext_len % key_len)) % key_len
        key_len = len(key)
        padding_len = (key_len - (len(plaintext) % key_len)) % key_len
        expected = plaintext + ('X' * padding_len)
        
        assert decrypted == expected
    
    def test_columnar_pads_correctly(self):
        """Should pad plaintext to grid size."""
        key = "KEY"
        plaintext = "HELLO"  # Not divisible by 3
        
        ciphertext = columnar.encrypt(plaintext, key)
        decrypted = columnar.decrypt(ciphertext, key)
        
        # Should contain padding
        assert len(decrypted) % len(key) == 0


class TestDESCipher:
    """Test DES cipher directly."""
    
    def test_des_encrypt_decrypt_round_trip(self):
        """DES should recover plaintext after decryption."""
        key = "0123456789abcdef"  # 16 hex chars = 8 bytes
        plaintext = "HELLO WORLD"
        
        ciphertext = des_cipher.encrypt(plaintext, key)
        decrypted = des_cipher.decrypt(ciphertext, key)
        
        assert decrypted == plaintext
    
    def test_des_returns_hex_string(self):
        """DES encrypt should return hex string."""
        key = "0123456789abcdef"
        plaintext = "TEST"
        
        ciphertext = des_cipher.encrypt(plaintext, key)
        
        # Should be valid hex
        try:
            bytes.fromhex(ciphertext)
        except ValueError:
            assert False, "Ciphertext is not valid hex"


class TestPipeline:
    """Test the complete 3-layer pipeline."""
    
    def test_pipeline_full_round_trip(self):
        """All 3 layers should recover plaintext (after removing X padding)."""
        plaintext = "SECRET MESSAGE"
        
        ciphertext = pipeline.encrypt_text(plaintext)
        decrypted = pipeline.decrypt_text(ciphertext)
        
        # Pipeline processes uppercase letters only, removes spaces
        # X may be inserted for padding, so compare without X and spaces
        clean_decrypted = decrypted.replace('X', '').replace(' ', '')
        clean_plaintext = plaintext.upper().replace('X', '').replace(' ', '')
        assert clean_decrypted == clean_plaintext
    
    def test_pipeline_ciphertext_differs_from_plaintext(self):
        """Ciphertext should not contain plaintext."""
        plaintext = "HELLO"
        ciphertext = pipeline.encrypt_text(plaintext)
        
        assert plaintext.upper() not in ciphertext


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
