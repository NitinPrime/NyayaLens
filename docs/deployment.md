# Deploy NyayaLens

Repo: https://github.com/NitinPrime/NyayaLens

Deploy as two services:

- **Frontend** (Next.js) → Vercel
- **API + Postgres** (FastAPI) → Railway

Do not use local SQLite in production.

```
Browser
  → Vercel (apps/web)
  → Railway FastAPI (apps/api)
  → Railway PostgreSQL
```

## 0. Push latest code

The production API Dockerfile must be on GitHub before Railway builds.

```powershell
cd D:\NyayaLens
git add apps/api/Dockerfile railway.json apps/web/vercel.json docs/deployment.md
git commit -m "Add production Docker and deploy config"
git push origin main
```

## 1. Railway — database + API

1. Open [railway.app](https://railway.app) and sign in with GitHub.
2. **New Project** → **Deploy from GitHub repo** → `NitinPrime/NyayaLens`.
3. In the project, **Add Service** → **Database** → **PostgreSQL**.
4. Select the GitHub-connected **service** (the API). Confirm it uses `apps/api/Dockerfile` (see `railway.json`).
5. Open the API service → **Variables** → add:

| Name | Value |
|------|--------|
| `DATABASE_URL` | Postgres URL from Railway, with scheme `postgresql+asyncpg://` (not `postgresql://`) |
| `DATABASE_URL_SYNC` | Same URL with `postgresql://` |
| `CORS_ORIGINS` | `http://localhost:3000` for now; replace with the Vercel URL after step 2 |
| `JWT_SECRET_KEY` | A long random string |
| `API_SECRET_KEY` | A long random string |
| `LLM_PROVIDER` | `mock` (change to `openai` later) |
| `LLM_MODEL` | `gpt-4o-mini` |
| `LOG_LEVEL` | `INFO` |

**How to set `DATABASE_URL`:** copy Railway’s `DATABASE_URL` / `POSTGRES_URL`, then:

- Original: `postgresql://postgres:PASS@host:5432/railway`
- API async: `postgresql+asyncpg://postgres:PASS@host:5432/railway`

If the URL contains `sslmode=require`, keep it.

6. Deploy. Wait until it is live.
7. Open the API **public domain** (Settings → Networking → Generate domain), then visit:

`https://YOUR-API.up.railway.app/api/v1/health`

You should see `{"status":"healthy","service":"nyayalens-api"}`.

Legal seed data is loaded on first startup from `data/legal_sources/seed_sources.json`.

## 2. Vercel — website

1. Open [vercel.com](https://vercel.com) → **Add New** → **Project** → import `NitinPrime/NyayaLens`.
2. Set:
   - **Root Directory:** `apps/web`
   - **Framework:** Next.js
3. Environment variable:

| Name | Value |
|------|--------|
| `NEXT_PUBLIC_API_URL` | `https://YOUR-API.up.railway.app` (no trailing slash) |

4. Deploy. Copy the Vercel URL, e.g. `https://nyayalens.vercel.app`.
5. Back on Railway, set `CORS_ORIGINS` to that Vercel origin (comma-separate if you have a preview URL too):

```text
https://nyayalens.vercel.app
```

6. Redeploy the API (or wait for restart) so CORS updates.
7. Open the Vercel site → **Explore Demo**.

## 3. Optional: real LLM

On Railway, set:

```text
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
LLM_MODEL=gpt-4o-mini
```

Redeploy the API. Without this, Demo Mode still works using the mock provider.

## 4. If something fails

| Symptom | Fix |
|---------|-----|
| Vercel loads, Analyze fails | `NEXT_PUBLIC_API_URL` missing or has a trailing slash |
| Browser CORS error | `CORS_ORIGINS` must be the exact Vercel origin (`https://...`) |
| API 500 on analyze | `DATABASE_URL` must use `postgresql+asyncpg://` |
| Railway build can’t find schemas | Dockerfile must copy `packages/schemas` (already in `apps/api/Dockerfile`) |
| Health works, UI talks to localhost | Rebuild Vercel after setting `NEXT_PUBLIC_API_URL` (`NEXT_PUBLIC_*` is baked in at build time) |

## Local vs production

| | Local | Production |
|--|--------|------------|
| Frontend | `npm run dev` on :3000 | Vercel |
| API | uvicorn on :8000 | Railway |
| Database | SQLite file | PostgreSQL |
| LLM | mock | mock or OpenAI |
