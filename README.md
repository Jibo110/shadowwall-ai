# ShadowWall AI

> Real-time cyber deception dashboard with autonomous AI threat response.

## Architecture

- **Frontend**: React 18 + TypeScript + Zustand + WebSockets
- **Backend**: FastAPI + Python 3.12 + async SQLAlchemy
- **AI Agent**: LangGraph autonomous threat triage and response
- **Infrastructure**: PostgreSQL + Redis + Docker Compose
- **Security**: Zero Trust, JWT, Rate Limiting, OWASP Top 10

## Status

🚧 Active development — Day 1

## Local Setup

```bash
cp .env.example .env
# Fill in .env values
docker compose up -d
```
