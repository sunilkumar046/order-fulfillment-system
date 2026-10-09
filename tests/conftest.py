import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


# ============================================================
# Add project root to Python import path
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================
# Application imports
# ============================================================

from app.main import app as fastapi_app
from app.database.base import Base
from app.database.database import get_db
from app.models.role import Role

# Import all models so SQLAlchemy knows every table
import app.models


# ============================================================
# Test database configuration
# ============================================================

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")

if not TEST_DATABASE_URL:
    raise RuntimeError(
        "TEST_DATABASE_URL is not configured. "
        "Set it in PowerShell before running pytest."
    )


# ============================================================
# Test database engine
# ============================================================

test_engine = create_engine(
    TEST_DATABASE_URL,
    pool_pre_ping=True,
)

TestingSessionLocal = sessionmaker(
    bind=test_engine,
    autoflush=False,
    autocommit=False,
)


# ============================================================
# Create and remove test database tables
# ============================================================

@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """
    Create all tables before the test session
    and remove them after all tests finish.
    """

    Base.metadata.create_all(bind=test_engine)

    # --------------------------------------------------------
    # Seed required roles
    # --------------------------------------------------------

    db = TestingSessionLocal()

    try:
        required_roles = [
            "Admin",
            "Warehouse Manager",
            "Fulfillment Agent",
            "Customer",
        ]

        for role_name in required_roles:
            existing_role = (
                db.query(Role)
                .filter(Role.name == role_name)
                .first()
            )

            if not existing_role:
                db.add(Role(name=role_name))

        db.commit()

    finally:
        db.close()

    yield

    # Remove all test tables after tests finish
    Base.metadata.drop_all(bind=test_engine)


# ============================================================
# Database session fixture
# ============================================================

@pytest.fixture
def db_session():
    """
    Provides a database session for each test.
    """

    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.rollback()
        db.close()


# ============================================================
# FastAPI TestClient fixture
# ============================================================

@pytest.fixture
def client(db_session):
    """
    Override FastAPI's normal database dependency
    so tests use the test PostgreSQL database.
    """

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    fastapi_app.dependency_overrides[get_db] = override_get_db

    with TestClient(fastapi_app) as test_client:
        yield test_client

    fastapi_app.dependency_overrides.clear()