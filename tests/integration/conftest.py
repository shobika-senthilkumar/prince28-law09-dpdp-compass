import os

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker


@pytest.fixture(scope="session")
def database_url():
    return os.getenv(
        "TEST_DATABASE_URL",
        "postgresql://app:app@localhost:5433/app_test",  # pragma: allowlist secret
    )


@pytest.fixture(scope="session")
def engine(database_url):
    engine = create_engine(database_url, pool_pre_ping=True)

    try:
        with engine.connect():
            pass
    except Exception as exc:
        pytest.skip(f"Integration database unavailable: {exc}")

    yield engine
    engine.dispose()


@pytest.fixture
def db_session(engine):
    session_factory = sessionmaker(
        bind=engine,
        class_=Session,
        expire_on_commit=False,
    )

    with session_factory() as session:
        yield session
