# Setup Guide

This document walks through everything needed to run Kaikoo locally and deploy it to production.

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Clone the repository](#2-clone-the-repository)
3. [Database](#3-database)
4. [Backend setup](#4-backend-setup)
5. [Google Cloud Console](#5-google-cloud-console)
6. [Anthropic API key](#6-anthropic-api-key)
7. [Notion integration](#7-notion-integration)
8. [Frontend setup](#8-frontend-setup)
9. [Running locally](#9-running-locally)
10. [Running database migrations](#10-running-database-migrations)
11. [Deploying to production](#11-deploying-to-production)
12. [Post-deploy checklist](#12-post-deploy-checklist)
13. [Troubleshooting](#13-troubleshooting)

---

## 1. Prerequisites

| Tool | Minimum version | Notes |
|---|---|---|
| Python | 3.12 | Use `python3 --version` to check |
| Node.js | 20 LTS | Use `node --version` to check |
| npm | 10+ | Bundled with Node |
| PostgreSQL | 15 | Must be running locally for development |
| Git | Any | |

**macOS (Homebrew):**
```bash
brew install python@3.12 node postgresql@15
brew services start postgresql@15
```

**Ubuntu / Debian:**
```bash
sudo apt install python3.12 python3.12-venv nodejs npm postgresql-15
sudo systemctl start postgresql
```

---

## 2. Clone the Repository

```bash
git clone https://github.com/gorlasreekanth/Kaikoo.git
cd Kaikoo
```

---

## 3. Database

Create a local PostgreSQL database:

```bash
psql -U postgres -c "CREATE DATABASE kaikoo;"
# or, if your local user has superuser access:
createdb kaikoo
```

Note the connection string — you will need it in `backend/.env`:
```
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/kaikoo
```

Replace `postgres:postgres` with your actual PostgreSQL username and password.

---

## 4. Backend Setup

```bash
cd backend

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Generate secret keys
python scripts/generate_keys.py
# This outputs two lines — copy them into your .env file:
#   SECRET_KEY=...
#   FERNET_KEY=...

# Copy the example env file
cp .env.example .env
```

Edit `backend/.env` and fill in every value. The full reference is below.

### Backend environment variables

```bash
# ── App ──────────────────────────────────────────────────────────────────────
SECRET_KEY=<64-char hex — from generate_keys.py>
FERNET_KEY=<Fernet key — from generate_keys.py>
ENVIRONMENT=development
ALLOWED_ORIGINS=http://localhost:5173

# ── Database ─────────────────────────────────────────────────────────────────
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/kaikoo

# ── Google OAuth ─────────────────────────────────────────────────────────────
# (see Section 5 — Google Cloud Console)
GOOGLE_CLIENT_ID=<your_client_id>.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=<your_client_secret>
GOOGLE_REDIRECT_URI_CALENDAR=http://localhost:8000/api/v1/calendar/callback
GOOGLE_REDIRECT_URI_GMAIL=http://localhost:8000/api/v1/gmail/callback

# ── Anthropic ────────────────────────────────────────────────────────────────
# (see Section 6)
ANTHROPIC_API_KEY=sk-ant-api03-...

# ── Notion ───────────────────────────────────────────────────────────────────
# (see Section 7)
NOTION_CLIENT_ID=<your_notion_client_id>
NOTION_CLIENT_SECRET=<your_notion_client_secret>
NOTION_REDIRECT_URI=http://localhost:8000/api/v1/notion/callback

# ── JWT ──────────────────────────────────────────────────────────────────────
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=10080   # 7 days
```

---

## 5. Google Cloud Console

Kaikoo uses three Google OAuth scopes:

| Scope | Used for |
|---|---|
| `openid email profile` | Sign-in (ID token) |
| `https://www.googleapis.com/auth/calendar.events` | Creating calendar events |
| `https://www.googleapis.com/auth/gmail.send` | Sending / drafting emails |

### 5a. Create a project

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Click **Select a project → New project** — name it `Kaikoo`
3. Navigate to **APIs & Services → Library**
4. Enable **Google Calendar API** and **Gmail API**

### 5b. Configure the OAuth consent screen

1. Go to **APIs & Services → OAuth consent screen**
2. Choose **External** → **Create**
3. Fill in:
   - App name: `Kaikoo`
   - User support email: your email
   - Developer contact: your email
4. Click **Save and continue** through Scopes and Test users (add your own Google account as a test user)
5. Status can remain **Testing** while developing

### 5c. Create OAuth 2.0 credentials

1. Go to **APIs & Services → Credentials → Create credentials → OAuth client ID**
2. Application type: **Web application**
3. Name: `Kaikoo Web`
4. **Authorised JavaScript origins** (for the Google Sign-In button):
   ```
   http://localhost:5173
   ```
5. **Authorised redirect URIs** (for Calendar and Gmail OAuth callbacks):
   ```
   http://localhost:8000/api/v1/calendar/callback
   http://localhost:8000/api/v1/gmail/callback
   ```
6. Click **Create** — copy the **Client ID** and **Client Secret** into `backend/.env` and `frontend/.env`

> **Production:** repeat step 4-5 adding your production URLs (e.g., `https://kaikoo.vercel.app` and `https://your-backend.railway.app/api/v1/...`). You can add multiple origins/URIs to the same credential.

---

## 6. Anthropic API Key

1. Go to [console.anthropic.com](https://console.anthropic.com)
2. Navigate to **API keys → Create key**
3. Copy the key into `backend/.env` as `ANTHROPIC_API_KEY`

Kaikoo uses:
- `claude-haiku-4-5-20251001` for real-time note processing (fast, low latency)
- `claude-sonnet-4-6` for category summaries (higher quality)

Estimated costs at moderate personal use (50 notes/day, 5 summaries/day): < $1/month.

---

## 7. Notion Integration

1. Go to [notion.so/my-integrations](https://www.notion.so/my-integrations)
2. Click **New integration**
3. Name: `Kaikoo`, type: **Public**
4. Set the **Redirect URI** to:
   ```
   http://localhost:8000/api/v1/notion/callback
   ```
5. Copy the **Client ID** and **Internal Integration Secret** into `backend/.env`

> **Production:** update the redirect URI to `https://your-backend.railway.app/api/v1/notion/callback`

---

## 8. Frontend Setup

```bash
cd frontend
npm install
cp .env.example .env
```

Edit `frontend/.env`:

```bash
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_GOOGLE_CLIENT_ID=<same client ID from Section 5c>
```

---

## 9. Running Locally

Open two terminals.

**Terminal 1 — backend:**
```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`.
Interactive docs: `http://localhost:8000/docs`

**Terminal 2 — frontend:**
```bash
cd frontend
npm run dev
```

The app will be available at `http://localhost:5173`.

---

## 10. Running Database Migrations

Alembic manages all schema changes.

**Apply all migrations (first run):**
```bash
cd backend
source .venv/bin/activate
alembic upgrade head
```

**Check current revision:**
```bash
alembic current
```

**Create a new migration** (after changing a model):
```bash
alembic revision --autogenerate -m "describe the change"
alembic upgrade head
```

**Roll back one step:**
```bash
alembic downgrade -1
```

---

## 11. Deploying to Production

### 11a. Backend — Railway

1. Install the Railway CLI: `npm install -g @railway/cli`
2. Login: `railway login`
3. In the `backend/` directory:
   ```bash
   railway init           # creates a new project
   railway add            # add a PostgreSQL plugin
   railway up             # deploy the app
   ```
4. Set all environment variables in the Railway dashboard (**Variables** tab):
   ```
   SECRET_KEY=...
   FERNET_KEY=...
   ENVIRONMENT=production
   ALLOWED_ORIGINS=https://kaikoo.vercel.app
   DATABASE_URL=<Railway provides this automatically via $DATABASE_URL>
   GOOGLE_CLIENT_ID=...
   GOOGLE_CLIENT_SECRET=...
   GOOGLE_REDIRECT_URI_CALENDAR=https://<your-railway-domain>/api/v1/calendar/callback
   GOOGLE_REDIRECT_URI_GMAIL=https://<your-railway-domain>/api/v1/gmail/callback
   ANTHROPIC_API_KEY=...
   NOTION_CLIENT_ID=...
   NOTION_CLIENT_SECRET=...
   NOTION_REDIRECT_URI=https://<your-railway-domain>/api/v1/notion/callback
   JWT_ALGORITHM=HS256
   JWT_EXPIRE_MINUTES=10080
   ```
5. Run migrations against the production database:
   ```bash
   railway run alembic upgrade head
   ```

### 11b. Frontend — Vercel

1. Install Vercel CLI: `npm install -g vercel`
2. In the `frontend/` directory:
   ```bash
   vercel
   ```
3. Follow the prompts (link to your Vercel account, set root directory to `frontend/`)
4. Set environment variables in the Vercel dashboard (**Settings → Environment Variables**):
   ```
   VITE_API_BASE_URL=https://<your-railway-domain>/api/v1
   VITE_GOOGLE_CLIENT_ID=<same client ID>
   ```
5. Redeploy: `vercel --prod`

The `frontend/vercel.json` already contains the SPA rewrite rule so all routes fall back to `index.html`.

---

## 12. Post-Deploy Checklist

After deploying, update all OAuth redirect URIs to use the production URLs:

- [ ] **Google Cloud Console** — add production origins and redirect URIs to the credential (Section 5c)
- [ ] **Notion** — update redirect URI in the integration settings (Section 7)
- [ ] **Railway variables** — verify all `*_REDIRECT_URI` values point to the Railway domain
- [ ] **Vercel variables** — verify `VITE_API_BASE_URL` points to Railway
- [ ] Test login end-to-end
- [ ] Test creating a note and verifying Claude assigns a category
- [ ] Test connecting Google Calendar (Settings page) and creating an event from a note
- [ ] Test connecting Gmail and sending a draft
- [ ] Test connecting Notion and verifying a page is created

---

## 13. Troubleshooting

**`CORS error` in the browser console**
- Check `ALLOWED_ORIGINS` in `backend/.env` includes `http://localhost:5173` (development) or your Vercel URL (production).

**`401 Unauthorized` on every request after login**
- The JWT may have been signed with a different `SECRET_KEY`. Regenerate keys (`python scripts/generate_keys.py`), update `.env`, and log in again.

**`Cannot connect to database`**
- Verify PostgreSQL is running: `pg_isready`
- Check `DATABASE_URL` — the driver prefix must be `postgresql+asyncpg://`, not `postgresql://`

**Google login button doesn't appear / shows error**
- `VITE_GOOGLE_CLIENT_ID` must be set before running `npm run dev` (Vite reads `.env` at startup)
- The origin `http://localhost:5173` must be in the **Authorised JavaScript origins** list in Google Cloud Console

**Google Calendar / Gmail OAuth returns `redirect_uri_mismatch`**
- The URI in `backend/.env` (`GOOGLE_REDIRECT_URI_CALENDAR` / `GOOGLE_REDIRECT_URI_GMAIL`) must exactly match one of the **Authorised redirect URIs** in Google Cloud Console — no trailing slashes

**`TypeError: AsyncClient.__init__() got an unexpected keyword argument 'proxies'`**
- Anthropic SDK and httpx version mismatch. Fix: `pip install "anthropic==0.49.0"`

**Notion sync silently fails**
- Check that the Notion integration has been granted access to at least one page in Notion (open any page → **...** menu → **Add connections** → select your integration)

**Voice input button not visible**
- Web Speech API is only available in Chrome and Edge. It will not appear in Firefox or Safari.
