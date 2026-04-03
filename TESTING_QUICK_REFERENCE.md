# FastAPI Testing - Quick Reference

## Installation
```bash
pip install pytest pytest-asyncio pytest-cov httpx
```

## Basic Test Structure

```python
from fastapi.testclient import TestClient
from app import app
import pytest

@pytest.fixture
def client():
    return TestClient(app)

def test_something(client):
    response = client.get("/api/status")
    assert response.status_code == 200
```

---

## Making Requests

### GET Request
```python
response = client.get("/api/status")
assert response.status_code == 200
```

### POST with JSON
```python
response = client.post(
    "/api/encrypt-text",
    json={"text": "HELLO"}
)
assert response.json()["status"] == "success"
```

### POST with File
```python
import io

file_obj = io.BytesIO(b"file content")
response = client.post(
    "/api/encrypt",
    files={"file": ("test.txt", file_obj, "text/plain")}
)
```

### POST with Headers
```python
response = client.post(
    "/api/endpoint",
    json={"data": "value"},
    headers={"X-Token": "secret"}
)
```

---

## Checking Responses

```python
response = client.get("/api/status")

# Status code
response.status_code  # 200
response.is_success   # True for 200-299
response.headers      # All headers
response.headers["content-type"]  # Specific header

# Body
response.json()       # Parse JSON
response.text         # Raw text
response.content      # Raw bytes

# URL
response.url          # Request URL
```

---

## Common Assertions

```python
# Status codes
assert response.status_code == 200
assert response.is_success
assert response.is_client_error  # 400-499
assert response.is_server_error  # 500-599

# Content
assert response.json() == expected_dict
assert "key" in response.json()
assert response.text == "expected text"

# Headers
assert "content-type" in response.headers
assert response.headers["content-type"] == "application/json"

# Existence
assert response.json().get("data") is not None
```

---

## Fixtures

### Basic Fixture
```python
@pytest.fixture
def sample_text():
    return "HELLO WORLD"

def test_with_fixture(client, sample_text):
    response = client.post(
        "/api/encrypt-text",
        json={"text": sample_text}
    )
    assert response.status_code == 200
```

### Fixture with Cleanup
```python
@pytest.fixture
def temp_file():
    # Setup
    file = Path("temp.txt")
    file.write_text("content")
    
    yield file  # Test runs here
    
    # Cleanup
    file.unlink()
```

### Fixture with Parameters
```python
@pytest.fixture(params=["test1.txt", "test2.txt"])
def test_files(request):
    return request.param

def test_multiple_files(test_files):
    # Test runs twice, once for each file
    pass
```

---

## Parametrized Testing

```python
@pytest.mark.parametrize("text,expected_length", [
    ("HELLO", 10),      # Playfair doubles length
    ("WORLD", 10),
    ("", 2),            # Empty gets padded
])
def test_encryption_length(client, text, expected_length):
    response = client.post(
        "/api/encrypt-text",
        json={"text": text}
    )
    assert response.status_code == 200
    # Your assertions
```

---

## Test Classes

```python
class TestEncryption:
    """Group related tests"""
    
    def test_encrypt_returns_200(self, client):
        response = client.post("/api/encrypt-text", json={"text": "HELLO"})
        assert response.status_code == 200
    
    def test_decrypt_returns_200(self, client):
        response = client.post("/api/decrypt-text", json={"ciphertext": "abc123"})
        # Note: will fail, just demonstrating structure
```

---

## Error Testing

```python
def test_missing_field_returns_422(client):
    """Pydantic validates automatically"""
    response = client.post(
        "/api/encrypt-text",
        json={}  # Missing "text" field
    )
    assert response.status_code == 422

def test_wrong_type_returns_422(client):
    response = client.post(
        "/api/encrypt-text",
        json={"text": 123}  # Should be string
    )
    assert response.status_code == 422

def test_empty_file_returns_400(client):
    response = client.post("/api/encrypt")  # No file
    assert response.status_code == 400
```

---

## Round-Trip Testing

```python
def test_encrypt_decrypt_round_trip(client):
    """Verify data integrity"""
    original = "SECRET MESSAGE"
    
    # Encrypt
    enc_resp = client.post(
        "/api/encrypt-text",
        json={"text": original}
    )
    ciphertext = enc_resp.json()["ciphertext_full"]
    
    # Decrypt
    dec_resp = client.post(
        "/api/decrypt-text",
        json={"ciphertext": ciphertext}
    )
    decrypted = dec_resp.json()["plaintext"]
    
    # Verify
    assert decrypted == original
```

---

## Running Tests

```bash
# All tests
pytest tests/

# Verbose
pytest tests/ -v

# Specific file
pytest tests/test_api.py

# Specific test
pytest tests/test_api.py::TestStatusEndpoint::test_status_returns_200

# Pattern matching
pytest tests/ -k "encrypt"

# Stop on first failure
pytest tests/ -x

# Show output/print statements
pytest tests/ -s

# Coverage
pytest tests/ --cov=backend --cov=app

# HTML coverage report
pytest tests/ --cov=backend --cov=app --cov-report=html

# Parallel execution (install pytest-xdist first)
pytest tests/ -n auto
```

---

## Debugging Tests

```bash
# Print debug info
pytest tests/ -v -s

# Drop into debugger on failure
pytest tests/ --pdb

# Drop into debugger on test start
pytest tests/ --trace

# Show slowest tests
pytest tests/ --durations=10
```

---

## Markers

```python
# Define marker
@pytest.mark.slow
def test_slow_encryption(client):
    pass

# Run only marked tests
pytest tests/ -m slow

# Run excluding marked
pytest tests/ -m "not slow"

# Multiple markers
@pytest.mark.slow
@pytest.mark.integration
def test_full_pipeline(client):
    pass
```

---

## Dependency Overriding

```python
def override_get_keys():
    return {"playfair": "TEST", "columnar": "KEY", "des": "0123456789abcdef"}

# Use in tests
app.dependency_overrides[get_keys] = override_get_keys

# Run test...

# Clean up
app.dependency_overrides.clear()
```

---

## Example: Real Test

```python
def test_full_encryption_flow(client):
    """Complete user flow: status → encrypt → decrypt"""
    
    # 1. Check system status
    status_resp = client.get("/api/status")
    assert status_resp.status_code == 200
    assert status_resp.json()["status"] == "ready"
    
    # 2. Encrypt a message
    plaintext = "HELLO WORLD"
    encrypt_resp = client.post(
        "/api/encrypt-text",
        json={"text": plaintext}
    )
    assert encrypt_resp.status_code == 200
    ciphertext = encrypt_resp.json()["ciphertext_full"]
    
    # 3. Verify encryption worked
    assert ciphertext != plaintext.lower()
    assert len(ciphertext) > len(plaintext)  # Hex encoding expands
    
    # 4. Decrypt the message
    decrypt_resp = client.post(
        "/api/decrypt-text",
        json={"ciphertext": ciphertext}
    )
    assert decrypt_resp.status_code == 200
    decrypted = decrypt_resp.json()["plaintext"]
    
    # 5. Verify we recovered original
    assert decrypted == plaintext
```

---

## Tips & Tricks

### 1. Use conftest.py for shared fixtures
Keep common fixtures in `tests/conftest.py` so all tests can use them.

### 2. Organize tests in classes
Group related tests to improve readability.

### 3. One assertion per concept
```python
# Good
def test_response_contains_fields(client):
    response = client.get("/api/status")
    assert "status" in response.json()
    assert "pipeline" in response.json()

# Also good - separate tests
def test_response_has_status_field(client):
    assert "status" in client.get("/api/status").json()

def test_response_has_pipeline_field(client):
    assert "pipeline" in client.get("/api/status").json()
```

### 4. Use descriptive names
```python
# Good
def test_encrypt_returns_different_ciphertext_for_different_messages(client):
    pass

# Also good - shorter
def test_different_messages_produce_different_ciphertexts(client):
    pass
```

### 5. Test edge cases
- Empty strings
- Very long strings
- Special characters
- Maximum file size
- Rapid successive requests

---

## Resources

- [FastAPI Testing](https://fastapi.tiangolo.com/advanced/testing-dependencies/)
- [Pytest Docs](https://docs.pytest.org/)
- [TestClient](https://docs.starlette.io/testclient/)
- [Httpx](https://www.python-httpx.org/)
