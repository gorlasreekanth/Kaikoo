# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Kaikoo is a minimalist personal assistant web app: users capture thoughts via text or voice, Claude auto-categorizes them and extracts intents (calendar events, emails), and the app syncs to Notion. Stack: React 19 + Vite (frontend), FastAPI (backend), PostgreSQL, Anthropic Claude API.

## Commands

### Local Development

```bash
npm run dev          # Full stack via Docker Compose (postgres + backend + frontend)
npm run servers      # Backend + frontend without Docker (requires local postgres)
npm run backend      # FastAPI only: cd backend && uvicorn app.main:app --reload --port 8000
npm run frontend     # Vite dev server only: cd frontend && npm run dev
```

### Frontend

```bash
cd frontend
npm run build        # TypeScript compile + Vite build
npm run lint         # ESLint check
npm run test         # Vitest (run once)
npm run test:watch   # Vitest watch mode
npm run test:coverage
```

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Database migrations
alembic upgrade head                      # Apply all pending migrations
alembic revision --autogenerate -m "desc" # Create migration from model changes
```

### Running a Single Frontend Test

```bash
cd frontend && npx vitest run src/path/to/test.test.tsx
```

## Architecture

### High-Level Flow

```
Browser → React (Vite/Vercel) → FastAPI (Railway) → PostgreSQL (Supabase)
                                      ↓                ├── APAC (ap-south-1)
                               Anthropic Claude API     └── NOAM (us-west-2)
                               Google Calendar / Gmail
                               Notion API
```

Users are pinned to a region (APAC or NOAM) at first login based on browser timezone. The region is encoded in the JWT and used to route all subsequent DB queries.

### Note Creation Data Flow (critical path)

1. `POST /api/v1/notes` with text content
2. JWT verified → User loaded
3. User's existing categories + recent note snippets sent to **Claude Haiku** as context
4. Single Claude call returns structured JSON: `{ category, is_new_category, append_to_note_id, intent }`
5. Note created or appended in DB; category `note_count` denormalized counter updated
6. Notion sync attempted (best-effort — DB commit not blocked by Notion failure)
7. Frontend receives note + optional `action` (calendar event or email draft)
8. If action present, confirmation modal shown before executing

### Frontend Structure

- **`src/api/`** — Axios client + typed API modules (auth, notes, categories, summaries, calendar, gmail, notion, integrations)
- **`src/store/`** — Zustand auth store (persisted to localStorage)
- **`src/hooks/`** — `useNotes`, `useCategories`, `useVoiceInput` (TanStack Query wraps all server state)
- **`src/pages/`** — `DashboardPage`, `CategoryPage`, `SummaryPage`, `SettingsPage`, `LoginPage`
- **`src/components/`** — `AppShell` + `Sidebar` + `TopBar` layout; `NoteInput`, `NoteList`, `NoteCard`; integration dialogs

Routes: `/login` → Google OAuth; `/` → all notes; `/category/:id`; `/summary/:id`; `/settings`

### Backend Structure

- **`app/main.py`** — FastAPI app, CORS middleware, 8 router includes
- **`app/routers/`** — One file per domain: `auth`, `notes`, `categories`, `summaries`, `calendar`, `gmail`, `notion`, `integrations`
- **`app/services/`** — Business logic: `claude_service`, `auth_service`, `calendar_service`, `gmail_service`, `notion_service`
- **`app/models/`** — SQLAlchemy ORM: `User`, `Category`, `Note`, `Integration`
- **`app/schemas/`** — Pydantic request/response types
- **`app/deps.py`** — `get_current_user` + `get_db` (region-aware) + `get_all_regions` FastAPI dependencies
- **`app/config.py`** — `Settings` (Pydantic BaseSettings reads from `.env` + `.secrets`)
- **`app/utils/geo.py`** — Timezone-to-region mapping for new user assignment
- **`app/utils/token_crypto.py`** — Fernet encrypt/decrypt for stored OAuth tokens

All API routes are prefixed `/api/v1/`.

### AI Models

- **`claude-haiku-4-5-20251001`** — Note processing (every save, optimized for latency/cost)
- **`claude-sonnet-4-6`** — Category summaries (on-demand, higher quality)

### Auth Flow

Google Sign-In (`id_token`) → `POST /api/v1/auth/google` → backend verifies with `google.oauth2.id_token.verify_oauth2_token()` → issues own JWT (HS256, 7-day TTL via `SECRET_KEY`) → stored in Zustand (localStorage). All subsequent requests use `Authorization: Bearer <jwt>`.

OAuth tokens for Calendar/Gmail/Notion are stored in the `integrations` table Fernet-encrypted using `FERNET_KEY`.

## Environment Setup

### 1. Root environment (Docker Compose)

Copy `.env.example` → `.env` for Docker Compose variables.

### 2. Backend config (`backend/.env`)

Copy `backend/.env.example` → `backend/.env`. Required settings: `SECRET_KEY`, `FERNET_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `ALLOWED_ORIGINS`.

### 3. Database passwords (`backend/.secrets`)

**This file is required for Supabase connectivity.** Copy `backend/.secrets.example` → `backend/.secrets` and fill in the Supabase database passwords.

```bash
cp backend/.secrets.example backend/.secrets
```

Find the passwords in each Supabase project: **Dashboard → Settings → Database → Connection string**.

| Variable | Description |
|---|---|
| `SUPABASE_DB_PASSWORD_APAC` | Database password for the APAC (India) Supabase project |
| `SUPABASE_DB_PASSWORD_NOAM` | Database password for the NOAM (US) Supabase project |

The `.secrets` file is gitignored and must never be committed. The `.env` file contains connection details (project refs, pooler hosts) but no passwords.

### Multi-Region Database

The backend connects to two Supabase PostgreSQL instances (APAC and NOAM). Users are pinned to a region at first login based on their browser timezone. Configuration is split across two files:

- **`backend/.env`** — Supabase project refs, pooler hosts, port (non-secret)
- **`backend/.secrets`** — Database passwords only (secret, gitignored)

Pydantic loads both files: `SettingsConfigDict(env_file=(".env", ".secrets"))`.

To run without Supabase (local Postgres only), leave the `SUPABASE_*` fields empty — the backend falls back to `DATABASE_URL`.

## Testing Approach

Frontend tests use Vitest + `@testing-library/react` + MSW (Mock Service Worker) for API mocking. Test files live alongside source files or in `src/__tests__/`. Backend has no automated test runner configured; manual testing via FastAPI's `/docs` (Swagger UI).
