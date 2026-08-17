# Phase 0.1 Environment & Infrastructure Setup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Scaffold the monorepo structure (`apps/web`, `apps/api`, `packages/shared`), configure `docker-compose.yml` for PostgreSQL 16 + `pgvector`, MinIO, FastAPI API, and Vite Web, initialize Alembic migrations, and verify round-trip backend connectivity.

**Architecture:** Monorepo layout per `architecture.md` Section 3 with Docker Compose orchestration. FastAPI backend container running on port 8000, Vite React TS frontend container running on port 5173, Postgres 16 with `pgvector` on port 5432, and MinIO object storage on port 9000/9001.

**Tech Stack:** Docker Compose, Python 3.11, FastAPI, SQLAlchemy, Alembic, Vite, React 18, TypeScript, TailwindCSS v4, MinIO (boto3).

**Spec:** `phases.md` Section 0.1, `architecture.md` Sections 1 & 3, `rules.md`

## Global Constraints

- **Python Version:** 3.11
- **Database:** PostgreSQL 16 with `pgvector` extension
- **Storage:** MinIO S3-compatible bucket (`algolyra-documents`) via signed URLs
- **Environment Gating:** Auto-migration and auto-seeding on boot are strictly gated behind `if os.getenv("ENV") == "local":`
- **Error Handling:** Standardized API error responses (`{"error_code": "...", "message": "...", "details": {...}}`)

---

### Task 1: Monorepo Directory Restructuring & Shared Package

**Files:**
- Modify: `package.json` (update root package.json for workspaces)
- Create: `packages/shared/package.json`
- Create: `packages/shared/src/index.ts`
- Create: `apps/web/package.json` (moved/updated from root)
- Modify: `apps/web/vite.config.ts`

**Interfaces:**
- Consumes: Root dependencies
- Produces: `packages/shared` package for shared domain models/types across web and API.

- [ ] **Step 1: Create directory structure for packages/shared and apps/web**
  Create directories `packages/shared/src`, `apps/web`, `apps/api`.

- [ ] **Step 2: Setup packages/shared/package.json and index.ts**

```json
{
  "name": "@algolyra/shared",
  "version": "0.1.0",
  "main": "./src/index.ts",
  "types": "./src/index.ts",
  "private": true
}
```

```typescript
// packages/shared/src/index.ts
export interface HealthStatus {
  status: string;
  app: string;
  version: string;
  environment: string;
}

export type ClaimType = 'CARGO_DAMAGE' | 'SHORTAGE' | 'LOST_CARGO';
export type ClaimStatus = 'DRAFT' | 'UNDER_REVIEW' | 'APPROVED' | 'SUBMITTED';
```

- [ ] **Step 3: Update root package.json with npm workspaces**

```json
{
  "name": "algolyra-monorepo",
  "private": true,
  "version": "0.1.0",
  "workspaces": [
    "apps/*",
    "packages/*"
  ],
  "scripts": {
    "dev:web": "npm run dev --workspace=apps/web",
    "build:web": "npm run build --workspace=apps/web"
  }
}
```

- [ ] **Step 4: Verify monorepo structure setup**
  Run `npm install` to link workspace packages.

---

### Task 2: FastAPI Backend Scaffolding (`apps/api`)

**Files:**
- Create: `apps/api/requirements.txt`
- Create: `apps/api/main.py`
- Create: `apps/api/db/session.py`
- Create: `apps/api/alembic.ini`
- Create: `apps/api/db/migrations/env.py`
- Create: `apps/api/db/migrations/script.py.mako`
- Create: `apps/api/tests/test_health.py`

**Interfaces:**
- Consumes: `DATABASE_URL`, `ENV` from environment.
- Produces: `GET /api/health` returning JSON `HealthStatus`.

- [ ] **Step 1: Create apps/api/requirements.txt**

```text
fastapi>=0.110.0
uvicorn[standard]>=0.28.0
sqlalchemy>=2.0.28
alembic>=1.13.1
psycopg2-binary>=2.9.9
pydantic>=2.6.4
pydantic-settings>=2.2.1
boto3>=1.34.60
python-dateutil>=2.9.0
python-multipart>=0.0.9
pytest>=8.1.1
pytest-asyncio>=0.23.5
httpx>=0.27.0
```

- [ ] **Step 2: Create apps/api/db/session.py**

```python
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://postgres:postgres@localhost:5432/algolyra"
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

- [ ] **Step 3: Create apps/api/main.py**

```python
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(
    title="Algolyra / Marajet Cargo Claim Recovery API",
    version="0.1.0"
)

# CORS setup for Vite frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
```

- [ ] **Step 4: Create apps/api/tests/test_health.py**

```python
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["app"] == "Marajet API"
```

- [ ] **Step 5: Initialize Alembic configuration in apps/api/alembic.ini**

Create `apps/api/alembic.ini` and `apps/api/db/migrations/env.py` configured to load `Base.metadata` from `db.session`.

---

### Task 3: Infrastructure Configuration (`docker-compose.yml` & `.env.example`)

**Files:**
- Create: `.env.example`
- Create: `docker-compose.yml`
- Create: `apps/api/Dockerfile`
- Create: `apps/web/Dockerfile`

**Interfaces:**
- Consumes: Environment variables
- Produces: 4 orchestration containers (`postgres`, `minio`, `api`, `web`) plus `createbuckets` helper.

- [ ] **Step 1: Create .env.example**

```env
ENV=local
DATABASE_URL=postgresql+psycopg2://postgres:postgres@postgres:5432/algolyra
MINIO_ENDPOINT=http://minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=algolyra-documents
PORT=8000
```

- [ ] **Step 2: Create apps/api/Dockerfile**

```dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

- [ ] **Step 3: Create apps/web/Dockerfile**

```dockerfile
FROM node:20-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
```

- [ ] **Step 4: Create docker-compose.yml**

```yaml
version: '3.8'

services:
  postgres:
    image: pgvector/pgvector:pg16
    container_name: algolyra-postgres
    restart: always
    environment:
      POSTGRES_DB: algolyra
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres -d algolyra"]
      interval: 5s
      timeout: 5s
      retries: 5

  minio:
    image: minio/minio:RELEASE.2024-03-21T23-13-43Z
    container_name: algolyra-minio
    restart: always
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    command: server /data --console-address ":9001"
    ports:
      - "9000:9000"
      - "9001:9001"
    volumes:
      - minio_data:/data
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 5s
      timeout: 5s
      retries: 5

  createbuckets:
    image: minio/mc:RELEASE.2024-03-21T18-18-09Z
    container_name: algolyra-createbuckets
    depends_on:
      minio:
        condition: service_healthy
    entrypoint: >
      /bin/sh -c "
      /usr/bin/mc alias set myminio http://minio:9000 minioadmin minioadmin;
      /usr/bin/mc mb myminio/algolyra-documents --ignore-existing;
      /usr/bin/mc anonymous set private myminio/algolyra-documents;
      exit 0;
      "

  api:
    build:
      context: ./apps/api
      dockerfile: Dockerfile
    container_name: algolyra-api
    restart: always
    ports:
      - "8000:8000"
    environment:
      - ENV=local
      - DATABASE_URL=postgresql+psycopg2://postgres:postgres@postgres:5432/algolyra
      - MINIO_ENDPOINT=http://minio:9000
      - MINIO_ACCESS_KEY=minioadmin
      - MINIO_SECRET_KEY=minioadmin
      - MINIO_BUCKET=algolyra-documents
    volumes:
      - ./apps/api:/app
    depends_on:
      postgres:
        condition: service_healthy
      minio:
        condition: service_healthy

  web:
    build:
      context: ./apps/web
      dockerfile: Dockerfile
    container_name: algolyra-web
    restart: always
    ports:
      - "5173:5173"
    environment:
      - VITE_API_URL=http://localhost:8000
    volumes:
      - ./apps/web:/app
      - /app/node_modules
    depends_on:
      - api

volumes:
  postgres_data:
  minio_data:
```

---

### Task 4: Frontend API Client & Connection Verification

**Files:**
- Create: `apps/web/src/lib/api-client.ts`
- Modify: `apps/web/vite.config.ts`
- Modify: `apps/web/src/App.tsx`

**Interfaces:**
- Consumes: `GET /api/health` from API server.
- Produces: Visual health check badge on frontend dashboard.

- [ ] **Step 1: Create apps/web/src/lib/api-client.ts**

```typescript
import { HealthStatus } from '@algolyra/shared';

const API_BASE_URL = import.meta.env.VITE_API_URL || '';

export async function fetchHealthStatus(): Promise<HealthStatus> {
  const response = await fetch(`${API_BASE_URL}/api/health`);
  if (!response.ok) {
    throw new Error(`API health check failed: ${response.statusText}`);
  }
  return response.json();
}
```

- [ ] **Step 2: Configure Vite proxy in apps/web/vite.config.ts**

```typescript
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
});
```

- [ ] **Step 3: Update apps/web/src/App.tsx to display connection status**

Add API health status verification indicator showing real-time connectivity status to FastAPI backend.

---

### Task 5: End-to-End Verification & Validation

**Files:**
- Run: `docker compose up --build`
- Run: `pytest apps/api/tests`

- [ ] **Step 1: Test API pytest suite**
  Execute `pytest` on backend. Ensure `test_health.py` passes 100%.

- [ ] **Step 2: Test round-trip web to api health connection**
  Verify `http://localhost:5173` successfully connects to `http://localhost:8000/api/health`.

- [ ] **Step 3: Verify MinIO bucket creation**
  Verify bucket `algolyra-documents` is initialized in MinIO.
