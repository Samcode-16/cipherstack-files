"""
Example tests demonstrating various FastAPI testing techniques.

This file shows practical examples of:
1. Using TestClient for HTTP requests
2. Fixture-based test setup
3. Parametrized testing
4. Error handling testing
5. File upload testing
6. Round-trip verification
"""

import pytest
import io
from pathlib import Path
from fastapi.testclient import TestClient
from app import app


@pytest.fixture
def client():
    """Pytest fixture: create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture
def sample_messages():
    """Pytest fixture: sample test data reusable across tests"""
    return ["HELLO", "SECRET", "THE QUICK BROWN FOX"]


@pytest.fixture
def temp_text_file(tmp_path):
    """Pytest fixture: create a temporary file for testing"""
    file = tmp_path / "test.txt"
    file.write_text("This is test content for encryption")
    return file


# ============================================================================
# Example 1: Basic HTTP Request Testing
# ============================================================================

class ExampleBasicRequests:
    """Demonstrate basic HTTP request patterns"""
    
    def example_get_request(self, client):
        """Example: Making a GET request"""
        response = client.get("/api/status")
        
        # Check response status
        assert response.status_code == 200
        
        # Parse JSON response
        data = response.json()
        assert data["status"] == "ready"
        print(f"✓ Status endpoint returned: {data['status']}")
    
    def example_post_request_with_json(self, client):
        """Example: Making a POST request with JSON body"""
        response = client.post(
            "/api/encrypt-text",
            json={"text": "HELLO WORLD"}  # Request body
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "ciphertext_full" in data
        print(f"✓ Encryption successful, ciphertext length: {len(data['ciphertext_full'])}")
    
    def example_post_request_with_file(self, client, temp_text_file):
        """Example: Making a POST request with file upload"""
        with open(temp_text_file, "rb") as f:
            response = client.post(
                "/api/encrypt",
                files={"file": f}  # File upload
            )
        
        assert response.status_code == 200
        assert len(response.content) > 0
        print(f"✓ File encrypted, output size: {len(response.content)} bytes")


# ============================================================================
# Example 2: Using Fixtures for Reusable Test Data
# ============================================================================

class ExampleFixtures:
    """Demonstrate pytest fixture usage"""
    
    def example_with_simple_fixture(self, client, sample_messages):
        """Use fixture data in multiple places"""
        for message in sample_messages:
            response = client.post(
                "/api/encrypt-text",
                json={"text": message}
            )
            assert response.status_code == 200
        print(f"✓ Successfully encrypted {len(sample_messages)} messages")
    
    def example_with_file_fixture(self, client, temp_text_file):
        """Use temporary file fixture"""
        with open(temp_text_file, "rb") as f:
            response = client.post(
                "/api/encrypt",
                files={"file": f}
            )
        
        # File is automatically cleaned up after test
        assert response.status_code == 200
        print("✓ File encrypted and fixture cleaned up automatically")


# ============================================================================
# Example 3: Parametrized Testing (Same Test, Different Data)
# ============================================================================

class ExampleParametrized:
    """Demonstrate parametrized test execution"""
    
    @pytest.mark.parametrize("message", ["HELLO", "WORLD", "TEST"])
    def example_test_runs_3_times(self, client, message):
        """This test runs once for each value in the list"""
        response = client.post(
            "/api/encrypt-text",
            json={"text": message}
        )
        assert response.status_code == 200
        # Pytest runs this 3 times: once for "HELLO", once for "WORLD", once for "TEST"
    
    @pytest.mark.parametrize("length,message", [
        (5, "HELLO"),
        (10, "HELLOWORLD"),
        (3, "ABC"),
    ])
    def example_multiple_parameters(self, client, length, message):
        """Use multiple parameters per test iteration"""
        response = client.post(
            "/api/encrypt-text",
            json={"text": message}
        )
        assert response.status_code == 200
        # Runs 3 times with different (length, message) combinations


# ============================================================================
# Example 4: Testing Error Responses
# ============================================================================

class ExampleErrorHandling:
    """Demonstrate error testing patterns"""
    
    def example_test_400_error(self, client):
        """Test that API returns 400 for invalid input"""
        response = client.post(
            "/api/encrypt-text",
            json={"text": ""}  # Empty text should fail
        )
        
        assert response.status_code == 400
        assert "error" in response.json()
        print("✓ API correctly returned 400 for invalid input")
    
    def example_test_422_validation_error(self, client):
        """Test that FastAPI validates request schema"""
        response = client.post(
            "/api/encrypt-text",
            json={"wrong_field": "value"}  # Missing "text" field
        )
        
        assert response.status_code == 422  # Pydantic validation error
        print("✓ API correctly returned 422 for schema validation failure")
    
    def example_test_413_file_too_large(self, client):
        """Test file size validation"""
        # Create oversized file
        large_content = b"x" * (11 * 1024 * 1024)  # 11 MB
        response = client.post(
            "/api/encrypt",
            files={"file": ("large.txt", io.BytesIO(large_content))}
        )
        
        assert response.status_code == 413  # File too large
        print("✓ API correctly rejected oversized file")


# ============================================================================
# Example 5: Round-Trip Testing (Encrypt → Decrypt → Verify)
# ============================================================================

class ExampleRoundTrip:
    """Demonstrate round-trip encryption/decryption testing"""
    
    def example_text_round_trip(self, client):
        """Encrypt text and verify it can be decrypted correctly"""
        original = "SECRET MESSAGE"
        
        # Step 1: Encrypt
        encrypt_resp = client.post(
            "/api/encrypt-text",
            json={"text": original}
        )
        ciphertext = encrypt_resp.json()["ciphertext_full"]
        
        # Step 2: Verify ciphertext is different
        assert ciphertext != original.lower()
        
        # Step 3: Decrypt
        decrypt_resp = client.post(
            "/api/decrypt-text",
            json={"ciphertext": ciphertext}
        )
        decrypted = decrypt_resp.json()["plaintext"]
        
        # Step 4: Verify we got original back
        assert decrypted == original
        print(f"✓ Round-trip successful: '{original}' → encrypted → '{decrypted}'")
    
    def example_file_round_trip(self, client, temp_text_file):
        """Encrypt file and verify it can be decrypted correctly"""
        original_content = temp_text_file.read_text()
        
        # Encrypt
        with open(temp_text_file, "rb") as f:
            encrypt_resp = client.post(
                "/api/encrypt",
                files={"file": f}
            )
        
        # Decrypt
        encrypted_data = io.BytesIO(encrypt_resp.content)
        decrypt_resp = client.post(
            "/api/decrypt",
            files={"file": ("test.encrypted", encrypted_data)}
        )
        
        # Verify
        decrypted_content = decrypt_resp.content.decode("utf-8")
        assert decrypted_content == original_content
        print(f"✓ File round-trip successful: {len(original_content)} → encrypted → {len(decrypted_content)} bytes")


# ============================================================================
# Example 6: Response Inspection
# ============================================================================

class ExampleResponseInspection:
    """Demonstrate response object inspection"""
    
    def example_inspect_response(self, client):
        """Show what information is available in responses"""
        response = client.get("/api/status")
        
        # Status code
        print(f"Status Code: {response.status_code}")  # 200
        
        # Check if successful
        print(f"Is Success: {response.is_success}")  # True (200-299)
        
        # Headers
        print(f"Content-Type: {response.headers['content-type']}")  # application/json
        
        # Body
        data = response.json()
        print(f"Response Keys: {list(data.keys())}")
        
        # Raw text
        print(f"Response Text Length: {len(response.text)}")  # Raw text
        
        # Raw bytes
        print(f"Response Bytes Length: {len(response.content)}")  # Raw bytes


# ============================================================================
# Example 7: Test Classes and Organization
# ============================================================================

class ExampleTestOrganization:
    """Demonstrate organizing tests into logical groups"""
    
    def test_first_scenario(self, client):
        """Tests in a class share the fixture"""
        response = client.get("/api/status")
        assert response.status_code == 200
    
    def test_second_scenario(self, client):
        """Same client fixture used automatically"""
        response = client.post("/api/encrypt-text", json={"text": "HELLO"})
        assert response.status_code == 200


# ============================================================================
# Run This File to See Examples
# ============================================================================

if __name__ == "__main__":
    # Run with: pytest tests/examples.py -v -s
    # The -s flag shows print output
    pytest.main([__file__, "-v", "-s"])
