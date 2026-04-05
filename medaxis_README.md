# MedAxis Retail — Pharmacy Operations Platform
## Prototype v1.0

### Quick Start

#### Backend (FastAPI)
```bash
pip install fastapi uvicorn pydantic --break-system-packages
cd backend
uvicorn main:app --reload --port 8000
```

#### Frontend
```bash
# Open frontend/index.html directly in your browser
# OR serve with Python:
cd frontend
python3 -m http.server 3000
# Then open http://localhost:3000
```

> **Note**: The frontend has full mock data built-in.
> It works standalone without the backend for demo purposes.
> When the backend is running, it automatically uses live API calls.

---

### Demo Credentials

| Email | Password | Role |
|-------|----------|------|
| admin@medaxis.in | admin123 | Super Admin |
| supervisor@medaxis.in | super123 | Regional Supervisor |
| pharma@medaxis.in | pharma123 | Pharmacist (Store S001) |
| inventory@medaxis.in | inv123 | Inventory Controller (Store S002) |

---

### Features Implemented

#### Auth Service
- JWT-based login/logout
- Role-based access (4 roles)
- Token management

#### Inventory Service
- Stock levels across 5 demo stores
- 10 SKUs with categories
- Low-stock alert detection
- Batch/expiry tracking
- Inter-store transfer workflow (request → approve → dispatch)
- Demand forecast per SKU (AI-simulated)

#### Billing Service
- POS new sale with cart
- Multi-item invoices with GST
- Payment mode tracking
- Sales history

#### Reporting Service
- Executive dashboard with KPIs
- Daily revenue trend (7 days)
- Store revenue comparison
- Fast-moving product analysis
- Category mix

#### AI Insights Service
- Anomaly detection display (3 flagged events)
- Resolve anomaly workflow
- Conversational NLQ interface
- Keyword-based query engine (real impl: LangChain + Claude)
- Per-SKU demand forecast chart

---

### Full Stack (Production)

```
backend/
  main.py              ← Combined prototype (split into services in prod)
  requirements.txt     ← fastapi, uvicorn, sqlalchemy, pydantic, etc.

frontend/
  index.html           ← Single-file prototype
  (production: React + Vite + React Router)
```

### Production Stack
- **Backend**: FastAPI per microservice + PostgreSQL + Redis + Kafka
- **AI**: LangChain + Claude API + Prophet + scikit-learn (Isolation Forest)
- **Frontend**: React 18 + TanStack Query + Recharts + Tailwind
- **Infra**: Kubernetes + Helm + ArgoCD + Prometheus + Grafana
- **Auth**: JWT + pyotp (MFA) + HashiCorp Vault

### Requirements (backend)
```
fastapi>=0.111.0
uvicorn[standard]>=0.29.0
pydantic>=2.7.0
sqlalchemy[asyncio]>=2.0.0
asyncpg>=0.29.0
alembic>=1.13.0
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4
pyotp>=2.9.0
redis>=5.0.0
confluent-kafka>=2.4.0
celery>=5.4.0
pandas>=2.2.0
polars>=0.20.0
prophet>=1.1.5
scikit-learn>=1.4.0
langchain>=0.2.0
langchain-anthropic>=0.1.0
pgvector>=0.2.0
sentence-transformers>=2.7.0
guardrails-ai>=0.4.0
opentelemetry-sdk>=1.24.0
opentelemetry-instrumentation-fastapi>=0.45b0
prometheus-fastapi-instrumentator>=6.1.0
structlog>=24.1.0
sentry-sdk>=2.3.0
hvac>=2.1.0
reportlab>=4.1.0
httpx>=0.27.0
apscheduler>=3.10.0
```
