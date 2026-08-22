import os
import sys
import time
import logging
from typing import Optional, Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from app.models.telemetry_model import APITelemetryLog
from db.session import SessionLocal

logger = logging.getLogger("telemetry_middleware")


class TelemetryMiddleware(BaseHTTPMiddleware):
    """
    FastAPI / Starlette Middleware for non-blocking production telemetry.
    Measures endpoint latency, payload sizes, status codes, and scopes to organization_id.
    """

    def __init__(self, app, session_factory: Optional[Callable] = None):
        super().__init__(app)
        self.session_factory = session_factory or SessionLocal

    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.perf_counter()

        # Extract request size
        try:
            content_length = int(request.headers.get("content-length", 0))
        except (ValueError, TypeError):
            content_length = 0

        # Extract organization_id from header, state, or query params
        org_id = (
            request.headers.get("x-organization-id")
            or getattr(request.state, "organization_id", None)
            or request.query_params.get("organization_id")
            or request.query_params.get("org_id")
        )

        response: Optional[Response] = None
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        except Exception as exc:
            status_code = 500
            raise exc
        finally:
            latency_ms = (time.perf_counter() - start_time) * 1000.0

            # Attach performance header if response exists
            if response is not None:
                response.headers["X-Response-Time"] = f"{latency_ms:.2f}ms"

            # Determine response size
            response_bytes = 0
            if response is not None and hasattr(response, "headers"):
                try:
                    response_bytes = int(response.headers.get("content-length", 0))
                except (ValueError, TypeError):
                    response_bytes = 0

            # Non-blocking DB logging with isolated session
            try:
                session = self.session_factory()
                try:
                    log_entry = APITelemetryLog(
                        organization_id=org_id,
                        endpoint_path=request.url.path,
                        http_method=request.method,
                        status_code=status_code,
                        latency_ms=round(latency_ms, 3),
                        request_bytes=content_length,
                        response_bytes=response_bytes,
                    )
                    session.add(log_entry)
                    session.commit()
                finally:
                    session.close()
            except Exception as log_err:
                logger.warning(f"Telemetry logging failed safely: {log_err}")
