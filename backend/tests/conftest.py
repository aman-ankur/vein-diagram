import pytest
import os
import tempfile
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.database import Base, get_db
from app.main import app
from fastapi.testclient import TestClient

# Create a test database
TEST_DATABASE_URL = "sqlite:///./test.db"

@pytest.fixture(scope="function")
def test_db():
    """Create a test database and tables."""
    # Create the test database engine
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    
    # Create the tables
    Base.metadata.create_all(bind=engine)
    
    # Create a test session
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Override the get_db dependency
    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    
    yield engine
    
    # Drop the tables after the test
    Base.metadata.drop_all(bind=engine)
    
    # Remove the test database file
    if os.path.exists("./test.db"):
        os.remove("./test.db")

@pytest.fixture(scope="function")
def client(test_db):
    """Create a test client for the FastAPI app."""
    with TestClient(app) as client:
        yield client

@pytest.fixture(scope="function")
def sample_pdf():
    """Create a sample PDF file for testing."""
    # Create a temporary PDF file
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
        # Write some content to the file
        temp_file.write(b'%PDF-1.5\n%Test PDF file for testing')
        temp_file.flush()
        
        yield temp_file.name
        
        # Clean up the file after the test
        if os.path.exists(temp_file.name):
            os.remove(temp_file.name) 