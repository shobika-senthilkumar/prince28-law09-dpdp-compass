import os

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker


def get_database_url() -> str:
    """Return the configured PostgreSQL database URL."""
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise RuntimeError("DATABASE_URL is not configured")

    return database_url


engine = create_engine(
    get_database_url(),
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    class_=Session,
    expire_on_commit=False,
)
