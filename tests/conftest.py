"""
Pytest configuration file (conftest.py)

This file contains shared pytest fixtures and configuration that's available
to all test files in the project.
"""

import pytest
import sys
from pathlib import Path

# Add project root to path so imports work correctly
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture(scope="session")
def project_root():
    """Return the project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture
def temp_dir(tmp_path):
    """
    Provide a temporary directory for test files.
    
    This uses pytest's built-in tmp_path fixture which automatically
    cleans up after the test.
    """
    return tmp_path


@pytest.fixture
def cleanup_uploaded_files():
    """
    Cleanup uploaded/output files after tests.
    
    Yields to allow test execution, then cleans up after.
    """
    yield
    
    # Cleanup after test
    from pathlib import Path
    upload_dir = Path("uploads")
    output_dir = Path("outputs")
    
    for dir_path in [upload_dir, output_dir]:
        if dir_path.exists():
            for file in dir_path.glob("*"):
                if file.is_file():
                    try:
                        file.unlink()
                    except:
                        pass
