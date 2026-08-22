import datetime
import uuid
from sqlalchemy import Column, String, Integer, Float, DateTime
from db.session import Base


class APITelemetryLog(Base):
    """
    Production Telemetry Log table for tracking API latency, payload sizes,
    status code distributions, and endpoint performance metrics.
    """
    __tablename__ = "api_telemetry_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String(36), index=True, nullable=True)
    endpoint_path = Column(String(255), index=True, nullable=False)
    http_method = Column(String(10), nullable=False)
    status_code = Column(Integer, index=True, nullable=False)
    latency_ms = Column(Float, nullable=False)
    request_bytes = Column(Integer, nullable=False, default=0)
    response_bytes = Column(Integer, nullable=False, default=0)
    created_at = Column(
        DateTime(timezone=True),
        index=True,
        nullable=False,
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "organization_id": self.organization_id,
            "endpoint_path": self.endpoint_path,
            "http_method": self.http_method,
            "status_code": self.status_code,
            "latency_ms": round(self.latency_ms, 2),
            "request_bytes": self.request_bytes,
            "response_bytes": self.response_bytes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
