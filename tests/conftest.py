import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from bark.common.db import Base, get_session
from bark.main import app

# Separate test DB
test_engine = create_engine("sqlite:///test.db")
TestSession = sessionmaker(bind=test_engine)


@pytest.fixture
def db():
    Base.metadata.create_all(test_engine)
    session = TestSession()
    yield session
    session.close()
    Base.metadata.drop_all(test_engine)


@pytest.fixture
def client(db):
    def override_get_session():
        yield db

    app.dependency_overrides[get_session] = override_get_session
    yield TestClient(app)
    app.dependency_overrides.clear()
