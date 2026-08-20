import os
import sys
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

sys.path.insert(0, os.path.dirname(__file__))
from routers.documents import router as documents_router
from routers.claims import router as claims_router
from routers.tms import router as tms_router

app = FastAPI(
    title="Algolyra / Marajet Cargo Claim Recovery API",
    description="Operating layer for freight cargo claims recovery",
    version="0.1.0"
)

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
