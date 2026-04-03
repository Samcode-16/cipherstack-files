# 🧪 FastAPI Testing Guide

Complete guide to testing your 3-layer encryption pipeline using FastAPI's testing features.

## Quick Start

### 1. Install Test Dependencies
```bash
pip install pytest pytest-asyncio pytest-cov httpx
```

### 2. Run All Tests
```bash
pytest tests/ -v
```

### 3. Run with Coverage Report
```bash
pytest tests/ --cov=backend --cov=app --cov-report=html
```

---

## FastAPI Testing Features

### 1. **TestClient** - Synchronous HTTP Testing

The `TestClient` from `starlette.testclient` is the primary tool:

```python
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

# Make requests like a regular HTTP client
response = client.get("/api/status")
response = client.post("/api/encrypt-text", json={"text": "HELLO"})
response = client.post("/api/encrypt", files={"file": file_object})
```

**Key Points:**
- ✅ No server needed - tests run directly
- ✅ Full control over requests
- ✅ Can inspect responses completely

### 2. **Fixtures** - Reusable Test Setup

Use `@pytest.fixture` for common test data:

```python
@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def test_plaintext():
    return "HELLO WORLD"

# Use in tests:
def test_something(client, test_plaintext):
    response = client.post(...)
    assert response.status_code == 200
```

### 3. **Dependency Overriding** - Mock Dependencies

Override app dependencies for testing:

```python
from fastapi import Depends
from app import app

def override_get_query():
    return "test_query"

app.dependency_overrides[get_query] = override_get_query

# Your tests now use the mocked dependency
# Remember to clear overrides after:
app.dependency_overrides.clear()
```

### 4. **Pydantic Models** - Automatic Validation Testing

FastAPI automatically validates request bodies:

```python
# If you send wrong type, FastAPI returns 422:
response = client.post(
    "/api/encrypt-text",
    json={"text": 123}  # Wrong: should be string
)
assert response.status_code == 422
```

### 5. **Async Testing** - For Async Endpoints

Use `pytest-asyncio` for async endpoint testing:

```bash
pip install pytest-asyncio
```

```python
import pytest

@pytest.mark.asyncio
async def test_async_endpoint():
    # Your async test code here
    pass
```

---

## Test Organization

### File Structure
```
tests/
├── __init__.py
├── conftest.py              # Shared fixtures
├── test_api.py              # API endpoint tests (200+ lines)
├── test_auth.py             # Authentication tests (if needed)
├── test_security.py         # Security tests
└── integration/
    ├── test_encryption_pipeline.py
    ├── test_file_operations.py
    └── test_performance.py
```

### Test Class Organization
```python
class TestStatusEndpoint:
    """Group related tests in classes"""
    
    def test_status_returns_200(self, client):
        """Each test method tests one thing"""
        pass
    
    def test_status_has_required_fields(self, client):
        """Clear, descriptive test names"""
        pass
```

---

## Common Testing Patterns

### 1. **Testing API Endpoints**

```python
def test_encrypt_endpoint(client):
    """Test basic endpoint functionality"""
    response = client.post(
        "/api/encrypt-text",
        json={"text": "HELLO"}
    )
    
    # Check status
    assert response.status_code == 200
    
    # Check response structure
    data = response.json()
    assert "ciphertext_full" in data
    assert data["plaintext"] == "HELLO"
```

### 2. **Testing File Uploads**

```python
import io

def test_file_encryption(client):
    """Test file upload and encryption"""
    file_content = io.BytesIO(b"test content")
    
    response = client.post(
        "/api/encrypt",
        files={"file": ("test.txt", file_content, "text/plain")}
    )
    
    assert response.status_code == 200
    assert len(response.content) > 0
```

### 3. **Testing Error Handling**

```python
def test_encrypt_no_text_returns_400(client):
    """Test error when required field missing"""
    response = client.post(
        "/api/encrypt-text",
        json={"text": ""}
    )
    assert response.status_code == 400
    assert "error" in response.json()
```

### 4. **Round-Trip Testing**

```python
def test_encrypt_decrypt_round_trip(client):
    """Verify data integrity through encrypt/decrypt cycle"""
    original = "SECRET MESSAGE"
    
    # Encrypt
    encrypt_resp = client.post(
        "/api/encrypt-text",
        json={"text": original}
    )
    ciphertext = encrypt_resp.json()["ciphertext_full"]
    
    # Decrypt
    decrypt_resp = client.post(
        "/api/decrypt-text",
        json={"ciphertext": ciphertext}
    )
    decrypted = decrypt_resp.json()["plaintext"]
    
    # Verify
    assert decrypted == original
```

### 5. **Performance Testing**

```python
import time

def test_encryption_performance(client):
    """Ensure encryption completes in reasonable time"""
    start = time.time()
    
    response = client.post(
        "/api/encrypt-text",
        json={"text": "TEST" * 100}
    )
    
    elapsed = time.time() - start
    
    assert response.status_code == 200
    assert elapsed < 5.0  # Should complete in < 5 seconds
```

### 6. **Testing with Fixtures**

```python
@pytest.fixture
def sample_data():
    """Reusable test data"""
    return {
        "short": "HELLO",
        "long": "THE QUICK BROWN FOX" * 10,
        "special": "Message with numbers 123 and symbols !@#"
    }

def test_multiple_messages(client, sample_data):
    """Test with different message samples"""
    for name, message in sample_data.items():
        response = client.post(
            "/api/encrypt-text",
            json={"text": message}
        )
        assert response.status_code == 200, f"Failed for {name}"
```

---

## Running Tests

### Basic Commands

```bash
# Run all tests
pytest tests/

# Run with verbose output (shows each test)
pytest tests/ -v

# Run specific test file
pytest tests/test_api.py

# Run specific test class
pytest tests/test_api.py::TestStatusEndpoint

# Run specific test method
pytest tests/test_api.py::TestStatusEndpoint::test_status_returns_200

# Stop on first failure
pytest tests/ -x

# Show print statements
pytest tests/ -v -s

# Run tests in parallel (faster - requires pytest-xdist)
pytest tests/ -n auto
```

### Coverage Reports

```bash
# Generate coverage report
pytest tests/ --cov=backend --cov=app

# Generate HTML report (opens in browser: htmlcov/index.html)
pytest tests/ --cov=backend --cov=app --cov-report=html

# Show coverage percentage
pytest tests/ --cov=backend --cov-report=term-missing

# Only show lines not covered
pytest tests/ --cov=backend --cov-report=term-missing:skip-covered
```

### Markers and Selection

```bash
# Mark specific tests
@pytest.mark.slow
def test_large_file_encryption(client):
    pass

# Run only marked tests
pytest tests/ -m slow

# Run excluding marked tests
pytest tests/ -m "not slow"

# Mark multiple tests
@pytest.mark.parametrize("text", ["HELLO", "WORLD", "TEST"])
def test_various_texts(client, text):
    pass
```

---

## Testing Response Objects

### Inspecting Responses

```python
def test_response_details(client):
    response = client.get("/api/status")
    
    # Status code
    print(response.status_code)          # 200
    
    # JSON body
    print(response.json())               # {"status": "ready", ...}
    
    # Text body
    print(response.text)                 # Raw text
    
    # Headers
    print(response.headers)              # All response headers
    print(response.headers["content-type"])  # Specific header
    
    # Raw bytes
    print(response.content)              # Binary content
    
    # URL
    print(response.url)                  # Request URL
```

### Common Assertions

```python
# Status codes
assert response.status_code == 200
assert response.is_success  # 200-299
assert response.is_client_error  # 400-499
assert response.is_server_error  # 500-599

# Content
assert response.json() == expected_dict
assert response.text == expected_text
assert "key" in response.json()

# Headers
assert "content-type" in response.headers
assert "text/plain" in response.headers["content-type"]
```

---

## Fixture Best Practices

### Fixture Scopes

```python
# Function scope (default) - runs for each test
@pytest.fixture
def fresh_data():
    return {"value": 1}

# Class scope - runs once per test class
@pytest.fixture(scope="class")
def setup_database():
    db = connect()
    yield db
    db.close()

# Session scope - runs once per test session
@pytest.fixture(scope="session")
def app_config():
    return load_config()
```

### Fixture Cleanup

```python
# Yield for cleanup
@pytest.fixture
def temp_file():
    file = Path("temp.txt")
    file.write_text("content")
    
    yield file  # Test runs here
    
    # Cleanup after test
    file.unlink()

# Using context manager
@pytest.fixture
def client():
    with TestClient(app) as client:
        yield client
    # Auto cleanup after
```

---

## Parametrized Testing

Test multiple inputs with one test function:

```python
@pytest.mark.parametrize("plaintext,expected_type", [
    ("HELLO", str),
    ("WORLD", str),
    ("", str),
])
def test_encryption_types(client, plaintext, expected_type):
    """Test various inputs"""
    response = client.post(
        "/api/encrypt-text",
        json={"text": plaintext}
    )
    
    if plaintext:
        assert response.status_code == 200
    else:
        assert response.status_code == 400
```

---

## Testing Best Practices

### ✅ DO's

- ✅ Test one thing per test
- ✅ Use descriptive test names
- ✅ Use fixtures for reusable data
- ✅ Test both success and error cases
- ✅ Test edge cases (empty strings, large files, etc.)
- ✅ Keep tests independent
- ✅ Use meaningful assertions with messages

```python
def test_encryption(client):
    response = client.post(...)
    assert response.status_code == 200, "Should return 200 for valid input"
```

### ❌ DON'Ts

- ❌ Don't test implementation details
- ❌ Don't create test dependencies between tests
- ❌ Don't skip error testing
- ❌ Don't use magic numbers
- ❌ Don't test third-party libraries

---

## Example: Testing Your Encryption System

Here's a complete example testing your specific encryption pipeline:

```python
# tests/test_encryption_pipeline.py

class TestEncryptionPipeline:
    """Comprehensive encryption pipeline tests"""
    
    def test_playfair_layer_works(self):
        """Layer 1: Playfair substitution"""
        from backend import playfair
        
        key = "MONARCHY"
        plaintext = "HELLO"
        
        ciphertext = playfair.encrypt(plaintext, key)
        decrypted = playfair.decrypt(ciphertext, key)
        
        assert decrypted == plaintext
    
    def test_columnar_layer_works(self):
        """Layer 2: Columnar transposition"""
        from backend import columnar
        
        key = "SECRET"
        plaintext = "HELLOWORLD"
        
        ciphertext = columnar.encrypt(plaintext, key)
        decrypted = columnar.decrypt(ciphertext, key)
        
        assert decrypted == plaintext
    
    def test_des_layer_works(self):
        """Layer 3: DES encryption"""
        from backend import des_cipher
        
        key = "0123456789abcdef"
        plaintext = "HELLO"
        
        ciphertext = des_cipher.encrypt(plaintext, key)
        decrypted = des_cipher.decrypt(ciphertext, key)
        
        assert decrypted == plaintext
    
    def test_full_pipeline(self, client):
        """All 3 layers together via API"""
        messages = [
            "HELLO",
            "SECRET MESSAGE",
            "THE QUICK BROWN FOX"
        ]
        
        for msg in messages:
            # Encrypt
            enc = client.post("/api/encrypt-text", json={"text": msg})
            ct = enc.json()["ciphertext_full"]
            
            # Decrypt
            dec = client.post("/api/decrypt-text", json={"ciphertext": ct})
            pt = dec.json()["plaintext"]
            
            assert pt == msg, f"Round-trip failed for: {msg}"
```

---

## Continuous Integration (CI)

Run tests automatically on git push:

### GitHub Actions Example

Create `.github/workflows/tests.yml`:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.9
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov
      
      - name: Run tests
        run: pytest tests/ --cov=backend --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

---

## Troubleshooting

### Import Errors

**Problem:** `ModuleNotFoundError: No module named 'app'`

**Solution:** Make sure you're running from project root:
```bash
cd /path/to/File_Encrypt
pytest tests/
```

### Tests Pass Locally but Fail in CI

**Problem:** Environment differences

**Solution:** Commit `requirements.txt` and ensure it's installed in CI

### Fixtures Not Found

**Problem:** `fixture 'client' not found`

**Solution:** Ensure you have `conftest.py` in tests directory

### Tests Run Slowly

**Problem:** Tests taking too long

**Solution:** 
- Run tests in parallel: `pytest -n auto`
- Skip slow tests: `pytest -m "not slow"`
- Use `pytest --durations=10` to find slow tests

---

## Resources

- [FastAPI Testing Docs](https://fastapi.tiangolo.com/advanced/testing-dependencies/)
- [Pytest Official Docs](https://docs.pytest.org/)
- [TestClient Documentation](https://docs.starlette.io/testclient/)
- [Pytest Fixtures](https://docs.pytest.org/en/stable/fixture.html)

---

## Quick Reference

| Command | Purpose |
|---------|---------|
| `pytest tests/` | Run all tests |
| `pytest tests/ -v` | Verbose output |
| `pytest tests/ -x` | Stop on first failure |
| `pytest tests/ -k encrypt` | Run tests matching "encrypt" |
| `pytest tests/ --cov=backend` | Show coverage |
| `pytest tests/ --cov-report=html` | Generate HTML coverage |
| `pytest tests/ -m slow` | Run marked tests |
| `pytest tests/ -n auto` | Run in parallel |

---

## Next Steps

1. ✅ Install test dependencies: `pip install pytest pytest-asyncio pytest-cov`
2. ✅ Run existing tests: `pytest tests/ -v`
3. ✅ Check coverage: `pytest tests/ --cov-report=html`
4. ✅ Add more tests for edge cases
5. ✅ Set up CI/CD pipeline

Happy testing! 🎉
