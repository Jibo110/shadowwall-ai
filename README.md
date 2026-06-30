# ShadowWall AI 🛡️

> A production-grade cyber deception platform with autonomous AI threat analysis, real-time WebSocket event streaming, and a hardened REST API.

![Python](https://img.shields.io/badge/Python-3.12-blue?style=flat-square&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-green?style=flat-square&logo=fastapi)
![React](https://img.shields.io/badge/React-18-blue?style=flat-square&logo=react)
![LangGraph](https://img.shields.io/badge/LangGraph-0.1-purple?style=flat-square)
![Docker](https://img.shields.io/badge/Docker-Compose-blue?style=flat-square&logo=docker)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

## What Is ShadowWall AI?

ShadowWall AI is a **cyber deception system** that deploys honey tokens — fake credentials, API keys, and database URLs — across an environment and monitors them for unauthorized access. When a honey token is triggered, an autonomous **LangGraph AI agent** analyzes the threat, classifies the attacker, assigns severity, and generates a natural language incident report — all in real time.

The live dashboard updates instantly via WebSockets. No polling. No page refresh. Pure real-time.

---

## Architecture

┌─────────────────────────────────────────────────────────┐

│ React Dashboard │

│ TypeScript + Zustand + WebSockets │

└──────────────────────┬──────────────────────────────────┘

│ HTTP + WebSocket

┌──────────────────────▼──────────────────────────────────┐

│ FastAPI Backend │

│ Python 3.12 + Async SQLAlchemy │

│ ┌─────────────┐ ┌──────────────┐ ┌───────────────┐ │

│ │ REST API │ │ WebSocket │ │ LangGraph │ │

│ │ (JWT Auth) │ │ Manager │ │ AI Agent │ │

│ └─────────────┘ └──────────────┘ └───────────────┘ │

└──────────┬───────────────────────────────────┬──────────┘

│ │

┌──────────▼──────────┐ ┌──────────▼──────────┐

│ PostgreSQL │ │ Redis │

│ (Primary Store) │ │ (Pub/Sub Cache) │

└─────────────────────┘ └─────────────────────┘

## LangGraph Agent Pipeline

When a honey token is triggered, the agent runs this 5-node reasoning graph:

TRIGGER EVENT

│

▼

┌─────────────┐ ┌──────────────┐ ┌─────────────┐

│ ENRICH │────▶│ CLASSIFY │────▶│ ASSESS │

│ │ │ │ │ │

│ IP context │ │ Actor type │ │ Severity │

│ UA analysis │ │ Threat class │ │ Confidence │

└─────────────┘ └──────────────┘ └──────┬──────┘

│

┌──────────────┐ ┌───────▼──────┐

│ RESPOND │◀────│ REPORT │

│ │ │ │

│ Action plan │ │ NL incident │

│ Urgency level│ │ report │

└──────┬───────┘ └─────────────┘

│

▼

DB + WebSocket Broadcast

---

## Tech Stack

| Layer         | Technology                   | Purpose                    |
| ------------- | ---------------------------- | -------------------------- |
| Frontend      | React 18 + TypeScript + Vite | Real-time dashboard        |
| State         | Zustand                      | Global state management    |
| Styling       | Tailwind CSS                 | Cyber-themed UI            |
| Charts        | Recharts                     | Severity distribution      |
| Backend       | FastAPI + Python 3.12        | Async REST API             |
| ORM           | SQLAlchemy 2.0 (async)       | Database access layer      |
| Migrations    | Alembic                      | Schema version control     |
| AI Agent      | LangGraph + LangChain        | Autonomous threat analysis |
| LLM           | OpenAI GPT-4o                | Natural language reasoning |
| Auth          | JWT (python-jose) + bcrypt   | Stateless authentication   |
| Database      | PostgreSQL 16                | Primary data store         |
| Cache         | Redis 7                      | Pub/sub + hot cache        |
| Containers    | Docker + Docker Compose      | Infrastructure isolation   |
| Logging       | structlog                    | Structured JSON logging    |
| Rate Limiting | slowapi                      | Per-IP rate limiting       |

---

## Security Implementation

ShadowWall AI addresses the **OWASP Top 10**:

| Risk                          | Implementation                                               |
| ----------------------------- | ------------------------------------------------------------ |
| A01 Broken Access Control     | JWT auth on all endpoints, role-based access                 |
| A02 Cryptographic Failures    | bcrypt password hashing, JWT signing                         |
| A03 Injection                 | SQLAlchemy ORM (parameterized queries)                       |
| A04 Insecure Design           | Layered architecture, fail-fast config validation            |
| A05 Security Misconfiguration | Security headers middleware, docs disabled in prod           |
| A07 Auth Failures             | JWT expiry, refresh tokens, account lockout after 5 failures |
| A09 Logging Failures          | Structured JSON logs on every security event                 |

---

## Project Structure

shadowwall-ai/

├── backend/

│ ├── app/

│ │ ├── agent/ # LangGraph AI agent

│ │ │ ├── graph.py # State machine definition

│ │ │ ├── nodes/ # enrich, classify, assess, report, respond

│ │ │ ├── prompts/ # Versioned prompt templates

│ │ │ └── state.py # Typed agent state

│ │ ├── api/v1/ # REST endpoints + WebSocket

│ │ ├── core/ # Config, security, logging, middleware

│ │ ├── db/ # Models, repositories, migrations

│ │ └── services/ # Business logic layer

│ ├── Dockerfile

│ └── pyproject.toml

├── frontend/

│ ├── src/

│ │ ├── components/ # UI + dashboard components

│ │ ├── hooks/ # useWebSocket

│ │ ├── pages/ # Dashboard, Login

│ │ ├── services/ # API client

│ │ ├── stores/ # Zustand state

│ │ └── types/ # TypeScript interfaces

│ └── package.json

├── infra/

│ └── docker-compose.yml # PostgreSQL + Redis

└── docs/

└── architecture.md

---

## Quick Start

### Prerequisites

- Docker Desktop
- Python 3.12+
- Node.js 20+

### 1. Clone and configure

```bash
git clone https://github.com/Jibo110/shadowwall-ai.git
cd shadowwall-ai
cp backend/.env.example backend/.env
# Fill in your OpenAI API key and generate secret keys
```

### 2. Start infrastructure

```bash
cd infra
docker compose up -d
```

### 3. Start backend

```bash
cd backend
uv venv .venv --python 3.12
uv pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Start frontend

```bash
cd frontend
npm install
npm run dev
```

### 5. Open dashboard

http://localhost:5173

---

## Demo Access

A demo account is available for evaluating the platform:

| Field    | Value              |
| -------- | ------------------ |
| Email    | demo@shadowwall.io |
| Password | Demo2024!          |

> **Note:** This account has standard analyst permissions. Deploy tokens and trigger events to see the AI agent pipeline in action.

## API Endpoints

| Method | Endpoint                 | Auth | Description        |
| ------ | ------------------------ | ---- | ------------------ |
| POST   | `/api/v1/auth/register`  | ❌   | Create account     |
| POST   | `/api/v1/auth/login`     | ❌   | Get JWT tokens     |
| GET    | `/api/v1/auth/me`        | ✅   | Current user       |
| POST   | `/api/v1/tokens/`        | ✅   | Deploy honey token |
| GET    | `/api/v1/tokens/`        | ✅   | List all tokens    |
| PATCH  | `/api/v1/tokens/{id}`    | ✅   | Update token       |
| DELETE | `/api/v1/tokens/{id}`    | ✅   | Delete token       |
| POST   | `/api/v1/events/trigger` | ✅   | Record trigger     |
| GET    | `/api/v1/events/recent`  | ✅   | Recent events      |
| WS     | `/api/v1/ws`             | ❌   | Real-time stream   |
| GET    | `/health`                | ❌   | Health check       |

---

## Environment Variables

```bash
# Application
APP_ENV=development
APP_SECRET_KEY=          # openssl rand -hex 32
APP_DEBUG=false

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/shadowwall_db

# Redis
REDIS_URL=redis://:password@localhost:6379/0

# JWT
JWT_SECRET_KEY=          # openssl rand -hex 32
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# AI
OPENAI_API_KEY=          # platform.openai.com

# Security
ALLOWED_ORIGINS=http://localhost:5173
RATE_LIMIT_PER_MINUTE=60
```

---

## Key Design Decisions

**Why LangGraph over a simple LLM call?**
LangGraph provides a stateful, directed graph with typed state flowing between nodes. Each node has a single responsibility. The graph is inspectable, testable, and extensible — adding a new analysis step is adding one node and one edge.

**Why async throughout?**
FastAPI + asyncpg + async SQLAlchemy means the server never blocks on I/O. Under load, one thread handles thousands of concurrent connections.

**Why the Repository pattern?**
Routes never touch the database. Services never write SQL. Repositories are the only database-aware layer. This makes every layer independently testable and the codebase maintainable as it scales.

**Why JWT over sessions?**
Stateless auth means no server-side session store. Every API instance can validate any token independently — horizontal scaling with zero coordination.

---

## Author

**Jibran Khan** — Full-Stack Developer & AI Engineer

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-blue?style=flat-square&logo=linkedin)](https://linkedin.com/in/jibran-khan-5aa105150)
[![GitHub](https://img.shields.io/badge/GitHub-Follow-black?style=flat-square&logo=github)](https://github.com/Jibo110)

---

## License

MIT License — see [LICENSE](LICENSE) for details.
