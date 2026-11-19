import pytest
from fastapi.testclient import TestClient

from dpdpcompass.api.main import app


@pytest.fixture
def client():
    return TestClient(app)
