# Skill: setup-render

Deploy the FastAPI backend as a Render Web Service and the React frontend as a Render Static Site.

## Prerequisites
- Code is pushed to a GitHub repository.
- Supabase (or another database) is already provisioned and you have the production `DATABASE_URL`.

---

## Backend — Web Service

### 1. Create the Web Service
In the Render dashboard → **New → Web Service** → connect your GitHub repo.

| Setting | Value |
|---|---|
| **Root directory** | `backend` |
| **Runtime** | Python |
| **Build command** | `pip install uv && uv sync --no-dev` |
| **Start command** | `uv run python -m app.main` |
| **Instance type** | Free (or higher for production) |

> Render sets `PORT` automatically. Make sure `settings.port` reads from the `PORT` env var so the app binds to the correct port.

### 2. Set environment variables
In the Web Service → **Environment**, add every variable from `.env.example` with production values:

| Key | Value |
|---|---|
| `APP_ENV` | `production` |
| `SECRET_KEY` | a long random string |
| `DATABASE_URL` | Supabase transaction pooler URL (port 6543, `postgresql+asyncpg://`) |
| `ANTHROPIC_API_KEY` | your Anthropic key |
| `ANTHROPIC_MODEL` | `claude-sonnet-4-6` |
| `ALLOWED_ORIGINS` | the Render static site URL (set after the frontend is deployed) |
| `LOG_LEVEL` | `INFO` |

### 3. Deploy
Render auto-deploys on every push to the connected branch. The first deploy happens immediately after the service is created. Check **Logs** in the dashboard for startup errors.

Note the backend URL (e.g. `https://your-app.onrender.com`) — you'll need it for the frontend.

---

## Frontend — Static Site

### 1. Set the API base URL
In `frontend/`, create or update the environment variable file for production:

```
# frontend/.env.production
VITE_API_URL=https://your-app.onrender.com
```

Make sure all API calls in the React app read from `import.meta.env.VITE_API_URL`.

### 2. Create the Static Site
In the Render dashboard → **New → Static Site** → connect the same GitHub repo.

| Setting | Value |
|---|---|
| **Root directory** | `frontend` |
| **Build command** | `npm ci && npm run build` |
| **Publish directory** | `dist` |

### 3. Set environment variables
In the Static Site → **Environment**:

| Key | Value |
|---|---|
| `VITE_API_URL` | backend Web Service URL |

### 4. Update CORS on the backend
Go back to the backend Web Service → **Environment** and set:

```
ALLOWED_ORIGINS=https://your-frontend.onrender.com
```

Trigger a redeploy (or it will pick up on the next push).

---

## Verify the deployment
1. Open the frontend URL — the React app should load.
2. Trigger an action that calls the API — check the backend logs in Render for the request.
3. If you see CORS errors in the browser console, confirm `ALLOWED_ORIGINS` matches the frontend URL exactly (no trailing slash).

## Notes
- Free-tier Web Services spin down after 15 minutes of inactivity and take ~30s to cold-start. Upgrade to a paid instance to avoid this in production.
- Render injects `PORT` — the app must bind to `0.0.0.0` and read the port from the env. Hardcoding `8000` will cause the health check to fail.
- Use Render's **Secret Files** (not environment variables) for any multi-line secrets or certificate files.
