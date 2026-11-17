import pytest
from fastapi.testclient import TestClient

from dpdpcompass.api.main import create_app


@pytest.fixture
def client():
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client
