import os
import sys
import io
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from main import app
from db.session import Base, get_db
from scripts.seed_demo_data import seed_data

# In-memory SQLite DB with StaticPool so all test connections share the same memory database
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture(autouse=True)
def setup_database():
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    seed_data(db)
    db.close()
    yield
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()

client = TestClient(app)

def test_upload_document_success():
    """Uploading a document to a valid claim succeeds with HTTP 201."""
    file_content = b"Sample Bill of Lading PDF Content for PRO-847293"
    files = {"file": ("BOL_847293.pdf", io.BytesIO(file_content), "application/pdf")}
    data = {"document_type": "BOL"}

    response = client.post("/api/claims/clm-847293/documents/upload", files=files, data=data)
    assert response.status_code == 201
    res_data = response.json()
    assert res_data["document_type"] == "BOL"
    assert res_data["filename"] == "BOL_847293.pdf"
    assert "sha256" in res_data
    assert res_data["extraction_status"] in ("uploaded", "processed")

def test_upload_duplicate_document_returns_409():
    """Uploading identical document payload twice returns HTTP 409 Conflict."""
    file_content = b"Identical Duplicate Payload Check SHA-256"
    files1 = {"file": ("POD_847293.pdf", io.BytesIO(file_content), "application/pdf")}
    data1 = {"document_type": "POD"}

    # First upload -> 201 Created
    res1 = client.post("/api/claims/clm-847293/documents/upload", files=files1, data=data1)
    assert res1.status_code == 201

    # Second upload with identical bytes -> 409 Conflict
    files2 = {"file": ("POD_847293_copy.pdf", io.BytesIO(file_content), "application/pdf")}
    data2 = {"document_type": "POD"}
    res2 = client.post("/api/claims/clm-847293/documents/upload", files=files2, data=data2)
    assert res2.status_code == 409
    err_data = res2.json()
    assert err_data["error_code"] == "duplicate_document"
    assert "Duplicate document fingerprint detected" in err_data["message"]

def test_get_document_signed_url():
    """Signed URL generation returns short-lived S3 URL path."""
    file_content = b"Invoice content for claim"
    files = {"file": ("Invoice_847293.pdf", io.BytesIO(file_content), "application/pdf")}
    data = {"document_type": "Invoice"}

    res = client.post("/api/claims/clm-847293/documents/upload", files=files, data=data)
    assert res.status_code == 201
    doc_id = res.json()["id"]

    url_res = client.get(f"/api/claims/clm-847293/documents/{doc_id}/url")
    assert url_res.status_code == 200
    url_data = url_res.json()
    assert "signed_url" in url_data
    assert doc_id in url_data["signed_url"]
