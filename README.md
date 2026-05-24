# Agent Webapp Template

A template for building full-stack web and iOS applications with a [Pydantic-AI](https://ai.pydantic.dev/) agent backend.

## Stack

- **React + Vite** — web frontend
- **Swift / SwiftUI** — iOS app
- **FastAPI** — async Python backend with dependency injection
- **Pydantic-AI** — structured LLM agent framework
- **Pydantic v2** — request/response schemas and settings
- **SQLAlchemy 2.0** — async ORM (add with `uv add sqlalchemy asyncpg`)
- **Supabase** — hosted PostgreSQL database and blob storage
- **Render** — hosting (backend as Web Service, frontend as Static Site)
- **uv** — dependency and virtual environment management
- **Python ≥ 3.12**

## Getting started

### 1. Clone and install dependencies

```bash
git clone https://github.com/tascoma/agent-webapp-template.git
cd agent-webapp-template
uv venv && uv sync
```

### 2. Configure environment

```bash
cp .env.example .env
```

Fill in the values in `.env`:

```env
APP_ENV=development
SECRET_KEY=              # openssl rand -hex 32
DATABASE_URL=            # see /setup-supabase skill
ANTHROPIC_API_KEY=       # from console.anthropic.com
```

### 3. Run the backend

```bash
cd backend
uv run python -m app.main
```

### 4. Run the frontend

```bash
cd frontend
npm install
npm run dev
```

The Vite dev server proxies `/api/*` to `http://localhost:8000`.

## Project structure

```
agent-webapp-template/
├── .env.example
├── pyproject.toml
├── skills/                  # Claude Code task playbooks
├── frontend/                # React + Vite app
├── ios/                     # Swift iOS app
└── backend/
    ├── app/
    │   ├── main.py          # FastAPI app, CORS, lifespan
    │   ├── core/            # config.py, logging.py
    │   ├── agents/          # Pydantic-AI agent definitions
    │   ├── dependencies/    # Shared Depends() factories
    │   ├── databases/       # SQLAlchemy engine and session factory
    │   ├── routes/          # APIRouter modules (one per resource)
    │   ├── models/          # SQLAlchemy ORM models
    │   ├── schemas/         # Pydantic request/response schemas
    │   └── services/        # Business logic layer
    ├── tests/
    ├── logs/
    └── uploads/
```

## Branch model

| Branch | Environment | Database |
|---|---|---|
| `main` | Production | Supabase prod |
| `dev` | Staging | Supabase staging |
| `feature/*` | Local | Local or staging |

Never commit directly to `main` or `dev`. Cut feature branches from `dev`, PR to `dev`, then PR to `main` to promote to production.

## Skills

This repo ships Claude Code skills in `skills/` for common tasks:

| Skill | What it does |
|---|---|
| `/setup` | First-time project bootstrap |
| `/add-resource` | Add a full CRUD resource |
| `/add-agent` | Add a new Pydantic-AI agent |
| `/setup-supabase` | Connect to a Supabase database |
| `/setup-render` | Deploy to Render |
| `/setup-ios` | Initialize the iOS Xcode project |
| `/add-ios-feature` | Add a screen or feature to the iOS app |
| `/github-workflow` | Branch strategy and PR flow |
| `/mcp-supabase` | Manage Supabase via MCP |
| `/mcp-render` | Manage Render via MCP |
| `/setup-storage` | Set up Supabase Storage for file uploads |
| `/add-auth` | Add Supabase Auth (backend, React, iOS) |
| `/add-migration` | Set up Alembic for schema migrations |
| `/setup-frontend` | Wire up the React app |
| `/add-frontend-feature` | Add a page or feature to the React frontend |
| `/add-tests` | Set up the pytest suite |
| `/setup-ci` | Add GitHub Actions CI and auto-deploy |

See [CLAUDE.md](CLAUDE.md) for full context on how this project is structured.
