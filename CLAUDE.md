# CLAUDE.md

Template for building a React + FastAPI web app with a Pydantic-AI agent backend.

## Behavior

- **Simplicity first.** Prefer the smallest solution that works. No premature abstractions or speculative flexibility.
- **Test before closing.** Run or write a test for every change before reporting it done.
- **Follow best practices.** Match the conventions and patterns already in the codebase. When in doubt, prefer the idiomatic approach for the language or framework in use.

## Tech stack

- **React** — web frontend UI (`frontend/`); Vite dev server proxies `/api/*` to `http://localhost:8000`
- **Swift / SwiftUI** — iOS app (`ios/`)
- **FastAPI** — async web framework with dependency injection (`backend/`); run with `uv run python -m app.main` from `backend/`
- **Pydantic v2** — request/response schemas and settings (`BaseSettings`); run tests with `uv run pytest` from `backend/`
- **Pydantic-AI** — agent framework for structured LLM interactions; `backend/app/agents/agent.py` is a working example
- **SQLAlchemy 2.0** — async ORM (`backend/app/databases/`); not pre-installed — add with `uv add sqlalchemy asyncpg` when setting up the database
- **Supabase** — hosted PostgreSQL database and blob storage; connection URL goes in `DATABASE_URL`, storage wired via `SUPABASE_URL` + `SUPABASE_SERVICE_ROLE_KEY`
- **Render** — hosting platform; backend as a Web Service, frontend as a Static Site
- **Python stdlib `logging`** — configured in `backend/app/core/logging.py`
- **uv** — package manager and virtual environment tool (replaces pip + venv)
- **Python ≥ 3.12** — enforced via `.python-version`

## Project structure

```
agent-webapp-template/
├── .env.example             # env var shape (.env is gitignored)
├── pyproject.toml           # project dependencies
├── skills/                  # task playbooks (see below)
├── frontend/                # React web app
├── ios/                     # Swift iOS app
└── backend/
    ├── app/
    │   ├── main.py          # FastAPI app, routers, lifespan, CORS
    │   ├── core/            # config.py, logging.py
    │   ├── databases/       # async engine, session factory, Base
    │   ├── dependencies/    # Depends() factories
    │   ├── routes/          # one APIRouter per resource
    │   ├── models/          # SQLAlchemy ORM models
    │   ├── schemas/         # Pydantic request/response schemas
    │   ├── agents/          # Pydantic-AI agent definitions
    │   └── services/        # business logic
    ├── tests/
    ├── logs/                # runtime output (gitignored)
    └── uploads/             # user uploads (gitignored)
```

## Skills

Invoke these for step-by-step procedures:

| Skill | When to use |
|---|---|
| `/setup` | First-time project bootstrap: venv, env, settings, logging, database, main.py |
| `/add-resource` | Add a full CRUD resource: model, schema, dep, service, router, tests |
| `/add-agent` | Add a new Pydantic-AI agent with tools and dependency wiring |
| `/setup-supabase` | Connect the app to a Supabase PostgreSQL database |
| `/setup-render` | Deploy the backend and frontend to Render |
| `/setup-ios` | Create the Xcode project and wire up the API client in `ios/` |
| `/add-ios-feature` | Add a new screen or feature to the iOS app |
| `/github-workflow` | Branch strategy, PR flow, and environment promotion |
| `/mcp-supabase` | Use the Supabase MCP to manage the database without leaving the editor |
| `/mcp-render` | Use the Render MCP to manage services and deployments without leaving the editor |
| `/setup-storage` | Set up Supabase Storage for file uploads |
| `/add-auth` | Add Supabase Auth: JWT verification, `current_user` dependency, protected routes, frontend and iOS auth flow |
| `/add-migration` | Set up Alembic and manage schema migrations |
| `/setup-frontend` | Wire up the React app: API client, env config, routing, auth state |
| `/add-frontend-feature` | Add a page or feature to the React frontend |
| `/add-tests` | Set up the pytest suite and write tests for a route module |
| `/setup-ci` | Add GitHub Actions for CI and auto-deploy to Render |

## Branches and environments

| Branch | Environment | Database |
|---|---|---|
| `main` | Production (Render prod services) | Supabase prod project |
| `dev` | Staging (Render staging services) | Supabase staging project |
| `feature/*` | Local only | Local or staging DB |

Never commit directly to `main` or `dev`. All work starts on a feature branch cut from `dev`, goes to `dev` via PR, then to `main` via PR when ready to ship.

