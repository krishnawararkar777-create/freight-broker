import datetime
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.session import Base
from app.models.telemetry_model import APITelemetryLog


def test_api_telemetry_model_creation():
    """Verify APITelemetryLog table schema instantiates and queries cleanly."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    log = APITelemetryLog(
        organization_id="org-apex-001",
        endpoint_path="/api/claims",
        http_method="POST",
        status_code=201,
        latency_ms=45.2,
        request_bytes=1024,
        response_bytes=2048,
    )
    session.add(log)
    session.commit()

    retrieved = session.query(APITelemetryLog).first()
    assert retrieved is not None
    assert retrieved.endpoint_path == "/api/claims"
    assert retrieved.http_method == "POST"
    assert retrieved.status_code == 201
    assert abs(retrieved.latency_ms - 45.2) < 0.01
    assert retrieved.request_bytes == 1024
    assert retrieved.response_bytes == 2048

    dict_repr = retrieved.to_dict()
    assert dict_repr["endpoint_path"] == "/api/claims"
    assert dict_repr["latency_ms"] == 45.2
    session.close()
