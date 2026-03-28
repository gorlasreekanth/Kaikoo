# Prerequisites

Everything you need before running `npm run dev`.

---

## 1. Install Docker Desktop

Docker runs all three services (PostgreSQL, backend, frontend) in containers.
No other local installs (Python, Node, Postgres) are needed.

Download: https://www.docker.com/products/docker-desktop

After installing, open Docker Desktop and make sure it is running (the whale icon is active in your menu bar) before running the app.

---

## 2. Install Node.js (for the `npm run dev` command only)

Node is only needed to execute `dev.sh` via npm. The app itself runs inside Docker.

Download: https://nodejs.org (LTS version)

Verify:
```bash
node -v   # v18 or higher
npm -v
```

---

## 3. Clone the repo

```bash
git clone https://github.com/gorlasreekanth/Kaikoo.git
cd Kaikoo
```

---

## 4. Get your API keys

### Anthropic (required — powers AI note processing)
1. Go to https://console.anthropic.com
2. Create an API key
3. Copy the `sk-ant-...` value

### Google OAuth (required — login + Calendar + Gmail)
1. Go to https://console.cloud.google.com
2. Create a project → APIs & Services → Credentials → Create OAuth 2.0 Client ID
3. Application type: **Web application**
4. Add these to **Authorised JavaScript origins**:
   ```
   http://localhost
   ```
5. Add these to **Authorised redirect URIs**:
   ```
   http://localhost:8000/api/v1/calendar/callback
   http://localhost:8000/api/v1/gmail/callback
   ```
6. Copy the **Client ID** and **Client Secret**
7. Enable these APIs in the Google Cloud Console:
   - Google Calendar API
   - Gmail API

### Notion (optional — only needed if you want Notion sync)
1. Go to https://www.notion.so/my-integrations
2. Create a new integration → copy Client ID and Client Secret
3. Set redirect URI to: `http://localhost:8000/api/v1/notion/callback`

---

## 5. Fill in your secrets

On first run, `npm run dev` will create `backend/.env` from the example and exit.
Open it and fill in your values:

```bash
# backend/.env

SECRET_KEY=        # generate with: openssl rand -hex 32
FERNET_KEY=        # generate with: python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
ENVIRONMENT=development
ALLOWED_ORIGINS=http://localhost

DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/kaikoo

GOOGLE_CLIENT_ID=          # from step 4
GOOGLE_CLIENT_SECRET=      # from step 4
GOOGLE_REDIRECT_URI_CALENDAR=http://localhost:8000/api/v1/calendar/callback
GOOGLE_REDIRECT_URI_GMAIL=http://localhost:8000/api/v1/gmail/callback

ANTHROPIC_API_KEY=         # from step 4

NOTION_CLIENT_ID=          # optional
NOTION_CLIENT_SECRET=      # optional
NOTION_REDIRECT_URI=http://localhost:8000/api/v1/notion/callback

JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=10080
```

> **Note:** `DATABASE_URL` must use `@db:5432` (Docker service name), not `@localhost:5432`.

---

## 6. Run

```bash
npm run dev
```

First run will take 2–3 minutes to build Docker images. Subsequent runs start in seconds.

---

## Local URLs

| Service | URL |
|---|---|
| **App (frontend)** | http://localhost |
| **Backend API** | http://localhost:8000/api/v1 |
| **API health check** | http://localhost:8000/api/v1/health |
| **PostgreSQL** | `localhost:5432` (user: `postgres`, db: `kaikoo`) |

---

## Dev bypass (skip Google login locally)

To skip the Google OAuth screen during local development:

1. Set in `frontend/.env` (create if missing):
   ```
   VITE_DEV_BYPASS_AUTH=true
   ```
2. Set in `backend/.env`:
   ```
   ENVIRONMENT=development
   ```
3. Re-run `npm run dev` — a **"Continue as Dev User"** button will appear on the login page.

---

## Stopping the app

```bash
# Stop containers (data is preserved)
Ctrl+C

# Stop and remove containers + volumes (wipes the database)
docker compose down -v
```
