import os
import sys
import pytest
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from db.session import Base
from app.models.telemetry_model import APITelemetryLog
from app.middleware.telemetry_middleware import TelemetryMiddleware


@pytest.fixture
def telemetry_test_app():
    """Build a test FastAPI application instrumented with TelemetryMiddleware."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    app = FastAPI()

    # Add middleware with custom session factory for testing
    app.add_middleware(TelemetryMiddleware, session_factory=TestingSessionLocal)

    @app.get("/api/test-endpoint")
    async def sample_get():
        return {"status": "success", "message": "Telemetry operational"}

    @app.post("/api/test-error")
    async def sample_error():
        return JSONResponse(status_code=400, content={"error": "bad_request"})

    return app, TestingSessionLocal


def test_telemetry_middleware_records_successful_request(telemetry_test_app):
    app, SessionLocal = telemetry_test_app
    client = TestClient(app)

    response = client.get(
        "/api/test-endpoint",
        headers={"X-Organization-Id": "org-apex-001"}
    )
    assert response.status_code == 200
    assert "X-Response-Time" in response.headers

    # Query DB for logged telemetry record
    session = SessionLocal()
    logs = session.query(APITelemetryLog).all()
    assert len(logs) == 1
    log = logs[0]
    assert log.endpoint_path == "/api/test-endpoint"
    assert log.http_method == "GET"
    assert log.status_code == 200
    assert log.organization_id == "org-apex-001"
    assert log.latency_ms > 0.0
    session.close()


def test_telemetry_middleware_records_error_request(telemetry_test_app):
    app, SessionLocal = telemetry_test_app
    client = TestClient(app)

    response = client.post(
        "/api/test-error",
        headers={"X-Organization-Id": "org-apex-002"}
    )
    assert response.status_code == 400

    session = SessionLocal()
    logs = session.query(APITelemetryLog).filter(APITelemetryLog.status_code == 400).all()
    assert len(logs) == 1
    log = logs[0]
    assert log.endpoint_path == "/api/test-error"
    assert log.http_method == "POST"
    assert log.status_code == 400
    assert log.organization_id == "org-apex-002"
    session.close()
