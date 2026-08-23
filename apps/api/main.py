import os
import sys
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

sys.path.insert(0, os.path.dirname(__file__))
from app.middleware.telemetry_middleware import TelemetryMiddleware
from routers.documents import router as documents_router
from routers.claims import router as claims_router
from routers.tms import router as tms_router
from routers.edi import router as edi_router
from routers.telemetry import router as telemetry_router
from routers.salvage import router as salvage_router
from routers.carrier_risk import router as carrier_risk_router
from routers.legal_cases import router as legal_cases_router
from routers.tariff_guardian import router as tariff_guardian_router
from routers.shipper import router as shipper_router

from db.session import Base, engine
from app.models.domain_models import *
from app.models.telemetry_model import *

app = FastAPI(
    title="Algolyra / Marajet Cargo Claim Recovery API",
    description="Operating layer for freight cargo claims recovery",
    version="0.1.0"
)

@app.on_event("startup")
def on_startup():
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        print(f"Table creation check warning: {e}")

# Telemetry middleware for API latency and error logging
app.add_middleware(TelemetryMiddleware)

# CORS setup to allow request from Vite React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(documents_router)
app.include_router(claims_router)
app.include_router(tms_router)
app.include_router(edi_router)
app.include_router(telemetry_router)
app.include_router(salvage_router)
app.include_router(carrier_risk_router)
app.include_router(legal_cases_router)
app.include_router(tariff_guardian_router)
app.include_router(shipper_router)

class HealthResponse(BaseModel):
    status: str
    app: str
    version: str
    environment: str

@app.get("/api/health", response_model=HealthResponse)
def health_check():
    return HealthResponse(
        status="ok",
        app="Marajet API",
        version="0.1.0",
        environment=os.getenv("ENV", "local")
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Pass-through structured HTTP exception details."""
    if isinstance(exc.detail, dict):
        return JSONResponse(status_code=exc.status_code, content=exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={"error_code": "http_error", "message": str(exc.detail)}
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Standardized API error response shape per rules.md Section 5."""
    return JSONResponse(
        status_code=500,
        content={
            "error_code": "internal_error",
            "message": "An unexpected error occurred",
            "details": {"exception": str(exc)}
        }
    )
