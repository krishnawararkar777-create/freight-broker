# Task 1 Brief: Monorepo Directory Restructuring & Shared Package

## Goal
Scaffold the monorepo directory layout (`apps/web`, `apps/api`, `packages/shared`) per `architecture.md` Section 3 and establish the `@algolyra/shared` package.

## Target Files
- `package.json` (Modify root for npm workspaces)
- `packages/shared/package.json` (New)
- `packages/shared/src/index.ts` (New)
- Move existing Vite frontend app into `apps/web` (Move/Create)
- `apps/web/package.json` (New/Updated for workspace)
- `apps/web/vite.config.ts` (Updated)

## Implementation Details

### 1. `packages/shared/package.json`
```json
{
  "name": "@algolyra/shared",
  "version": "0.1.0",
  "main": "./src/index.ts",
  "types": "./src/index.ts",
  "private": true
}
```

### 2. `packages/shared/src/index.ts`
```typescript
export interface HealthStatus {
  status: string;
  app: string;
  version: string;
  environment: string;
}

export type ClaimType = 'CARGO_DAMAGE' | 'SHORTAGE' | 'LOST_CARGO';
export type ClaimStatus = 'DRAFT' | 'UNDER_REVIEW' | 'APPROVED' | 'SUBMITTED';
```

### 3. Move frontend to `apps/web`
Move `src/`, `public/`, `index.html`, `vite.config.ts`, `tsconfig.json`, `tsconfig.app.json`, `tsconfig.node.json`, `.oxlintrc.json` into `apps/web/`.

### 4. `apps/web/package.json`
```json
{
  "name": "@algolyra/web",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build",
    "lint": "oxlint",
    "preview": "vite preview"
  },
  "dependencies": {
    "@algolyra/shared": "*",
    "lucide-react": "^1.31.0",
    "react": "^19.2.8",
    "react-dom": "^19.2.8"
  },
  "devDependencies": {
    "@tailwindcss/vite": "^4.3.3",
    "@types/node": "^24.13.3",
    "@types/react": "^19.2.17",
    "@types/react-dom": "^19.2.3",
    "@vitejs/plugin-react": "^6.0.4",
    "oxlint": "^1.75.0",
    "tailwindcss": "^4.3.3",
    "typescript": "~6.0.2",
    "vite": "^8.2.0"
  }
}
```

### 5. Root `package.json`
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

## Report Contract
Save the full execution report to `c:\Users\krish\Downloads\FREIGHT BROKER\.superpowers\sdd\2026-08-16-phase-0-1-infrastructure\task-1-report.md`.
Return status: DONE, DONE_WITH_CONCERNS, NEEDS_CONTEXT, or BLOCKED.
