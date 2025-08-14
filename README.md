## Blantyre Synod CCAP Schools – Multi‑Tenant School Management System

This repository contains a modern, secure, multi‑tenant School Management System tailored for Blantyre Synod CCAP Schools. Each school operates as an isolated tenant within a shared platform.

### Highlights
- Schema‑based multi‑tenancy on PostgreSQL for strong data isolation with centralized ops
- Web‑based, responsive UI (React + Vite + TypeScript + Chakra UI) with PWA support
- FastAPI backend with JWT auth, RBAC, and tenant‑aware DB sessions
- Core domains: Users/Roles, Students, Classrooms, Finance (Invoices/Payments), Messaging
- Tenant onboarding API that creates a dedicated schema and seeds defaults
- HQ super dashboard (public schema) with cross‑tenant visibility

### Tech Stack
- Backend: FastAPI, SQLAlchemy 2.x, PostgreSQL (psycopg3), Pydantic v2, python‑jose
- Frontend: React + Vite + TypeScript, Chakra UI, Axios, React Router, Vite PWA
- DevOps: Docker Compose (db, backend)

### Multi‑Tenancy Strategy (Why schema‑based?)
You can implement multi‑tenancy using:
- Database‑per‑tenant: strongest isolation but operationally heavy (connections, migrations)
- Schema‑per‑tenant (Chosen): excellent isolation with manageable ops; per‑tenant schemas, shared DB; simple “SET search_path” per request; easy to aggregate across tenants
- Row‑level: lowest operational overhead but requires stringent row‑level filtering in every query; harder to guarantee isolation and performance at scale

This system uses schema‑per‑tenant on PostgreSQL. Each school gets a dedicated schema with identical tables. The `public` schema stores global/HQ entities (e.g., `tenants` registry) and supports super‑admin analytics across schools.

### Project Structure
```
backend/
  app/
    api/
      routers/
    core/
    db/
    models/
    schemas/
    services/
    tenancy/
    main.py
  requirements.txt
  Dockerfile
frontend/
  src/
  index.html
  package.json
  vite.config.ts
docker-compose.yml
.env.example
```

### Getting Started (Local, with Docker for DB + Backend)
1) Copy envs and adjust as needed
```
cp .env.example .env
```

2) Start Postgres and Backend
```
docker compose --env-file env.sample up --build
```
Backend will listen on `http://localhost:8000`.

3) Frontend (dev mode)
```
cd frontend
npm install
npm run dev
```
Frontend dev server at `http://localhost:5173`.

Note: To override envs, copy `env.sample` to `.env` and edit.

### First‑Run Flow
1) Onboard a tenant (school) – create schema and seed roles/admin
```
POST http://localhost:8000/api/tenants/onboard
{
  "name": "St Andrews Primary",
  "slug": "standrews",
  "admin_email": "admin@standrews.mw",
  "admin_password": "ChangeMe!123"
}
```

2) Login (include X‑Tenant header)
```
POST http://localhost:8000/api/auth/login
Headers: X-Tenant: standrews
{
  "username": "admin@standrews.mw",
  "password": "ChangeMe!123"
}
```

3) Use token for subsequent requests (Authorization: Bearer <token>) and always send `X‑Tenant: <slug>` header.

### Security
- JWT auth with strong password hashing (bcrypt via Passlib)
- Role‑based access control enforced via FastAPI dependencies
- Per‑request tenant resolution (`X‑Tenant` header or subdomain parsing) and `SET LOCAL search_path` to prevent cross‑tenant leakage
- CORS configured for local dev; lock down origins in production

### Finance & Malawi Payments
The Finance module includes invoices, payments, and expenses. Payment integrations are structured behind a provider interface with stubs for:
- Airtel Money (Malawi)
- TNM Mpamba
- Bank integrations

Replace stubs with real provider SDK/API calls and configure credentials via environment variables.

### PWA & Offline Support
- Frontend includes Vite PWA plugin setup (install prompt, offline caching shell)
- Extend using background sync and IndexedDB for offline queues if needed

### Admin Super Dashboard (HQ)
- The `public` schema stores `tenants` and other HQ entities
- Aggregate analytics can be built by iterating tenant schemas and executing read‑only queries

### Environment Variables
See `.env.example` and `backend/app/core/config.py` for defaults and overrides. Minimum required:
- `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`
- `DATABASE_URL`
- `JWT_SECRET`, `JWT_ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`

### API Quick Reference
- `POST /api/tenants/onboard` – Create tenant, schema, seed roles and admin
- `POST /api/auth/login` – Obtain JWT (requires `X‑Tenant`)
- `GET /api/students` – List students (tenant‑scoped)
- `POST /api/finance/invoices` – Create invoice (tenant‑scoped)
- `POST /api/finance/payments` – Record payment (tenant‑scoped)

### Production Deployment
- Host on AWS/Azure/DO with managed Postgres (e.g., RDS)
- Use containerized FastAPI behind a reverse proxy (e.g., NGINX) + HTTPS via Let’s Encrypt
- Configure subdomain routing per tenant (e.g., `<slug>.schools.bccap.mw`) and set `X‑Tenant` at the edge or use subdomain resolver in middleware
- Enforce AOF/backup policies for Postgres and create migration pipelines (Alembic)

### License
Proprietary – Blantyre Synod CCAP Schools.


