# Repository Structure Guide

## Folder Organization

### `/tests/` - Automated Test Suite
All pytest-based test files are organized here. These are **automated tests** that verify the correctness and functionality of your encryption system.

**Files:**
- `test_api_formatting.py` - Tests for API response formatting
- `test_comprehensive_decryption.py` - Full decryption cycle tests
- `test_decrypt_*.py` - Decryption-specific test cases
- `test_encryption_flow.py` - End-to-end encryption workflow tests
- `test_playfair_*.py` - Playfair cipher algorithm tests
- Other test utilities...

**Usage:**
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_playfair_known.py

# Run tests with coverage
pytest --cov=backend tests/

# Run tests with specific markers
pytest -m encryption tests/
```

### `/debug/` - Debugging & Diagnostics Scripts
Scripts for **manual investigation and troubleshooting**. These are NOT automated tests but rather diagnostic tools for developers.

**Files:**
- `debug_corruption.py` - Diagnose file corruption issues
- `debug_detailed.py` - Detailed pipeline debugging
- `debug_pipeline.py` - Pipeline execution tracing
- `debug_playfair_issue.py` - Playfair cipher debugging

**Usage:**
```bash
# Run a debug script standalone
python debug/debug_detailed.py

# These scripts help identify:
# - Pipeline failures
# - Encryption/decryption bugs
# - Algorithm issues
# - Data corruption problems
```

## Why We Need Both Test and Debug Files

### **Test Files (`/tests/`)**

1. **Automated Validation**: Run repeatedly with `pytest` to catch regressions
2. **CI/CD Integration**: Can be integrated into continuous integration pipelines
3. **Documentation**: Test cases document expected behavior
4. **Coverage Metrics**: Help track code coverage and identify untested paths
5. **Regression Prevention**: Detect when new changes break existing functionality
6. **Reproducibility**: Standardized test environment across all machines

### **Debug Files (`/debug/`)**

1. **Manual Investigation**: For developers to step through problematic scenarios
2. **Ad-hoc Exploration**: Test specific edge cases or theories quickly
3. **Real-world Scenarios**: Reproduce production bugs in isolation
4. **Performance Analysis**: Profile slow operations
5. **Data Inspection**: Examine intermediate values during execution
6. **Rapid Iteration**: Faster feedback loop than writing formal test cases

### **The Complementary Relationship**

- **Tests** = Preventive (catch problems before they reach production)
- **Debug** = Detective (investigate problems when they occur)

**Example Workflow:**
```
1. User reports encryption issue
   ↓
2. Run debug/debug_pipeline.py to reproduce and understand
   ↓
3. Identify root cause (e.g., Playfair padding bug)
   ↓
4. Write test case (test_playfair_padding.py) to prevent regression
   ↓
5. Fix the bug
   ↓
6. Run pytest to verify all tests pass
```

## Recommended Development Practices

### When to Write Tests:
- ✅ Core algorithm correctness (encryption, decryption, key generation)
- ✅ API endpoints and request/response formats
- ✅ Data preservation (formatting, special characters)
- ✅ Error handling and edge cases
- ✅ Integration between components

### When to Write Debug Scripts:
- 🐛 Investigating unexpected production issues
- 🔍 Exploring new encryption modes before formalizing tests
- ⚡ Performance profiling and optimization
- 🧪 Testing complex scenarios with many variables
- 📊 Data analysis and inspection

---

**Structure Summary:**
```
File_Encrypt/
├── tests/
│   ├── test_api.py              # Existing tests
│   ├── test_playfair_*.py       # Cipher tests
│   ├── test_encryption_flow.py
│   └── ... (19 test files total)
│
├── debug/
│   ├── debug_corruption.py
│   ├── debug_detailed.py
│   ├── debug_pipeline.py
│   └── debug_playfair_issue.py
│
├── backend/
│   ├── format_preserving_encryption.py  # Core utility
│   ├── playfair.py
│   ├── des_cipher.py
│   └── ...
│
└── pytest.ini                   # Pytest configuration
```
