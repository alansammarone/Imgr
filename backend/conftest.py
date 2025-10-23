import sys
from pathlib import Path

# Add backend directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

import pytest
from fastapi.testclient import TestClient
from api.main import app


@pytest.fixture
def client():
    """Test client fixture for FastAPI app"""
    return TestClient(app)
