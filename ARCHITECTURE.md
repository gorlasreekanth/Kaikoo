# Architecture

This document describes the system design of Kaikoo: how the components fit together, how data flows through the system, and the key decisions behind each layer.

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Component Diagram](#2-component-diagram)
3. [Frontend Architecture](#3-frontend-architecture)
4. [Backend Architecture](#4-backend-architecture)
5. [Database Schema](#5-database-schema)
6. [AI Pipeline](#6-ai-pipeline)
7. [Authentication Flow](#7-authentication-flow)
8. [Integration Flows](#8-integration-flows)
9. [Security Model](#9-security-model)
10. [Deployment Architecture](#10-deployment-architecture)
11. [Key Design Decisions](#11-key-design-decisions)

---

## 1. System Overview

```
┌─────────────────────────────────────────────────────┐
│                   Browser (React)                   │
│  Login → Note Input → Category View → Settings      │
└────────────────┬────────────────────────────────────┘
                 │  HTTPS / REST JSON
                 ▼
┌─────────────────────────────────────────────────────┐
│              FastAPI Backend (Railway)              │
│  /api/v1/{auth,notes,categories,summaries,          │
│           calendar,gmail,notion,integrations}       │
└───────┬─────────────────┬───────────────────────────┘
        │                 │
        ▼                 ▼
┌──────────────┐   ┌────────────────────────────────┐
│  PostgreSQL  │   │        External APIs           │
│  (Railway)   │   │  Claude  │ Google  │  Notion   │
└──────────────┘   └────────────────────────────────┘
```

The frontend is a single-page React app deployed on Vercel. It communicates exclusively with the FastAPI backend over REST/JSON. The backend handles all business logic, AI calls, and third-party API calls — the browser never holds third-party API keys.

---

## 2. Component Diagram

```
App
├── GoogleOAuthProvider        (wraps entire app for login button)
├── QueryClientProvider        (TanStack Query — all server state)
├── ToastProvider              (global notification context)
└── RouterProvider
    ├── /login  →  LoginPage
    │              └── GoogleLogin button
    │
    └── ProtectedRoute  (redirects to /login if no JWT)
        └── AppShell
            ├── Sidebar
            │   ├── "All Notes" nav link
            │   ├── CategoryList   ← useCategories()
            │   │   └── CategoryItem × N
            │   └── Settings nav link
            ├── TopBar
            │   └── UserAvatar + logout
            └── <Outlet>
                ├── /             DashboardPage
                │   ├── NoteInput
                │   │   ├── <textarea>
                │   │   └── VoiceButton  ← useVoiceInput()
                │   ├── NoteList         ← useNotes()
                │   │   └── NoteCard × N
                │   └── ConfirmationModal  (conditional)
                │       ├── CalendarConfirm
                │       └── EmailConfirm
                ├── /category/:id   CategoryPage
                │   ├── NoteInput
                │   └── NoteList (filtered)
                ├── /summary/:id    SummaryPage
                │   └── Claude-generated prose
                └── /settings       SettingsPage
                    ├── IntegrationCard (Google Calendar)
                    ├── IntegrationCard (Gmail)
                    └── IntegrationCard (Notion)
```

---

## 3. Frontend Architecture

### State Management

| Concern | Tool | Persistence |
|---|---|---|
| Auth (JWT + user) | Zustand + `persist` middleware | `localStorage` |
| Server data (notes, categories) | TanStack Query | In-memory cache |
| Voice transcript | Local `useState` in `useVoiceInput` | None |
| Confirmation modal state | Local `useState` in `DashboardPage` | None |

### API Layer (`src/api/`)

All HTTP calls go through a single Axios instance (`client.ts`) which:
1. Reads the JWT from Zustand on every request via a request interceptor
2. Automatically calls `logout()` (clears token + redirects to `/login`) on any `401` response

### Route Protection

`ProtectedRoute` checks the Zustand store for a token. If absent, it renders `<Navigate to="/login" replace />` — no async call is needed.

### Voice Input (`useVoiceInput`)

Wraps the browser's `SpeechRecognition` / `webkitSpeechRecognition` API. The hook:
- Exposes `start()`, `stop()`, `reset()`, `isListening`, `transcript`, `isSupported`
- Only renders the mic button when `isSupported === true` (Chrome/Edge)
- Fires an `onTranscript` callback on final (non-interim) results, which updates the note textarea

### Tailwind CSS v4 Theme

Colours are defined as CSS custom properties under `@theme` in `index.css` and referenced throughout components as `bg-bg`, `text-text-muted`, `bg-accent`, etc.

```css
@theme {
  --color-bg: #0f0f0f;
  --color-surface: #1a1a1a;
  --color-accent: #7c6af7;
  /* ... */
}
```

---

## 4. Backend Architecture

### Request Lifecycle

```
Browser
  │
  ├─ POST /api/v1/notes  { content, source }
  │         │
  │         ├─ Dependency: get_current_user()
  │         │   └─ Decode JWT → load User from DB
  │         │
  │         ├─ Load user's categories + recent notes (for Claude context)
  │         │
  │         ├─ claude_service.process_note()   ← single Anthropic API call
  │         │   └─ Returns: { category, is_new_category,
  │         │                 append_to_note_id, intent }
  │         │
  │         ├─ DB: get-or-create Category
  │         ├─ DB: append-to or create Note
  │         ├─ (optional) notion_service.sync_note()  ← best-effort
  │         │
  │         └─ Return: { note, category, action? }
  │                    action = calendar | email payload, or null
  │
  └─ User sees ConfirmationModal if action is present
```

### Dependency Injection Pattern

Every protected route receives its dependencies via FastAPI's `Depends()`:

```python
@router.post("/notes")
async def create_note(
    body: NoteCreateRequest,
    db: AsyncSession = Depends(get_db),          # DB session
    current_user: User = Depends(get_current_user),  # verified user
):
```

`get_current_user` decodes the JWT and loads the user. Routes never accept `user_id` from the request body — identity always comes from the verified token.

### Async Database Access

SQLAlchemy is used in async mode with `asyncpg` as the driver. All DB calls use `await db.execute(select(...))` patterns. Sessions are provided per-request via `AsyncSessionLocal` and yielded by `get_db()`.

---

## 5. Database Schema

```
┌─────────────────────────────────────────────────────────┐
│ users                                                   │
│  id         UUID  PK                                    │
│  email      VARCHAR(255)  UNIQUE                        │
│  name       VARCHAR(255)                                │
│  avatar_url TEXT                                        │
│  google_id  VARCHAR(255)  UNIQUE                        │
│  created_at TIMESTAMPTZ                                 │
│  updated_at TIMESTAMPTZ                                 │
└──────────────────────┬──────────────────────────────────┘
                       │ 1:N
        ┌──────────────┼────────────────────────┐
        ▼              ▼                        ▼
┌─────────────┐  ┌─────────────┐  ┌────────────────────────────┐
│ categories  │  │   notes     │  │       integrations         │
│  id    UUID │  │  id    UUID │  │  id       UUID             │
│  user_id FK │  │  user_id FK │  │  user_id  FK               │
│  name       │  │  cat_id  FK │  │  service  VARCHAR(50)      │
│  color      │  │  content    │  │  (google_calendar|         │
│  note_count │  │  source     │  │   gmail|notion)            │
│  created_at │  │  created_at │  │  access_token  TEXT (enc.) │
└──────┬──────┘  │  updated_at │  │  refresh_token TEXT (enc.) │
       │ 1:N     └─────────────┘  │  token_expiry  TIMESTAMPTZ │
       └──────────────────────────│  scope                     │
                                  │  notion_workspace_id       │
                                  │  notion_default_page_id    │
                                  │  created_at / updated_at   │
                                  └────────────────────────────┘
```

### Key design choices

- **`note_count` on Category** is maintained by the notes router (increment on create, decrement on delete) to avoid a `COUNT(*)` subquery on every sidebar render.
- **OAuth tokens are encrypted at rest** using Fernet symmetric encryption before being stored in `integrations.access_token` / `refresh_token`. The `FERNET_KEY` in the environment is the only way to decrypt them.
- **Notes are stored flat** — there is no hierarchical structure. Claude assigns categories; the user never manually organises.

---

## 6. AI Pipeline

### Note Processing (called on every `POST /notes`)

**Model:** `claude-haiku-4-5-20251001` — chosen for low latency on the hot path (~300 ms).

**Single-call design:** One Claude call handles three decisions simultaneously to minimise perceived latency.

```
Input:
  - New note text
  - Existing categories + last 3 note snippets per category (max 200 chars each)
  - Today's date (for relative time parsing)

Claude output (strict JSON):
{
  "category":           "Work"      // name of category to use
  "is_new_category":    false        // create new category row?
  "append_to_note_id":  "<uuid>"    // append to existing note, or null
  "intent": {
    "type":     "calendar",
    "calendar": {
      "title":      "Sprint planning",
      "start_time": "2025-03-20T14:00:00",
      "end_time":   "2025-03-20T15:00:00",
      "description": "..."
    }
  }
}
```

**Continuation detection:** Claude sees recent note snippets per category. If the new note clearly continues an existing thought, `append_to_note_id` is set and the backend appends to that note's `content` field (newline-separated). This keeps related thoughts in a single note record.

**Fallback:** If the Claude call fails for any reason, the backend falls back to creating a "General" category note without any intent, so the user's input is never lost.

### Summarisation (on-demand via `GET /summaries/:category_id`)

**Model:** `claude-sonnet-4-6` — higher capability is acceptable since this is not on the hot path.

All notes in the category are loaded in chronological order and passed to Claude. The prompt asks for 2–4 paragraphs of prose identifying themes and action items. The response is returned directly to the frontend — summaries are not cached in the database.

---

## 7. Authentication Flow

```
1. User clicks "Sign in with Google" (frontend)
   └─ @react-oauth/google opens Google's consent dialog
   └─ On success, Google returns an id_token (signed JWT)

2. Frontend calls POST /api/v1/auth/google  { id_token }

3. Backend verifies the id_token:
   └─ google.oauth2.id_token.verify_oauth2_token()
   └─ Validates signature against Google's public keys
   └─ Checks audience matches GOOGLE_CLIENT_ID
   └─ Extracts: sub (google_id), email, name, picture

4. Backend upserts user row (create if new, update name/avatar if existing)

5. Backend issues its own JWT:
   └─ Payload: { sub: user.id, exp: now + 7 days }
   └─ Signed with SECRET_KEY (HS256)
   └─ Returns: { access_token, user }

6. Frontend stores access_token in Zustand (persisted to localStorage)
   └─ All subsequent requests include: Authorization: Bearer <access_token>

7. Backend validates the access_token on every protected route:
   └─ Decodes JWT, extracts user.id
   └─ Loads User row from DB
   └─ Injects as current_user into the route handler
```

**Why issue a backend JWT instead of passing the Google id_token directly?**
The Google id_token has a short TTL (~1 hour) and would require the frontend to refresh via Google on every expiry. A backend JWT with a 7-day TTL provides a stable session without a dependency on Google's token refresh at request time. The backend JWT also lets us add custom claims or revocation logic later.

---

## 8. Integration Flows

### Google Calendar / Gmail OAuth

Both Calendar and Gmail require additional OAuth scopes beyond the login `id_token`. The user grants them explicitly in Settings.

```
1. User clicks "Connect Google Calendar" in Settings
2. Frontend calls GET /api/v1/calendar/auth-url
3. Backend builds a Google authorization URL:
   - scopes: calendar.events
   - access_type: offline  (requests refresh_token)
   - prompt: consent
4. Frontend opens the URL in a popup window
5. User approves → Google redirects to /api/v1/calendar/callback?code=...
6. Backend exchanges code for access_token + refresh_token
7. Tokens are Fernet-encrypted and stored in integrations table
8. Frontend re-fetches /integrations → shows "Connected"
```

When creating an event, the backend:
1. Loads the integration row for the current user
2. Decrypts the access_token
3. Checks expiry — refreshes via Google if expired
4. Calls the Google Calendar API with `google-api-python-client`

Gmail follows the same pattern with `gmail.send` scope.

### Notion OAuth

Notion uses its own OAuth server (not Google's).

```
1. User clicks "Connect Notion" in Settings
2. Frontend calls GET /api/v1/notion/auth-url
3. Backend returns notion.com/v1/oauth/authorize?... URL
4. User approves → Notion redirects to /api/v1/notion/callback?code=...
5. Backend exchanges code for access_token + workspace_id
   (Notion tokens do not expire — no refresh_token needed)
6. Token is Fernet-encrypted and stored in integrations table
```

When a note is saved, the notes router attempts to sync it to Notion **after** the DB commit. This is best-effort — a Notion failure does not cause the note save to fail. The router calls `notion_service.sync_note_to_notion()` which:
1. Checks if a Notion page for this category already exists (`notion_default_page_id`)
2. If not, creates a new top-level Notion page titled with the category name
3. Appends the note content as a paragraph block
4. Stores the page ID in the integration row for future appends

---

## 9. Security Model

| Concern | Approach |
|---|---|
| Authentication | Backend-issued JWT (HS256, `SECRET_KEY`) |
| OAuth tokens at rest | Fernet symmetric encryption (`FERNET_KEY`) — tokens are never stored in plaintext |
| User isolation | Every DB query filters by `user_id` derived from the verified JWT — never from request body |
| CORS | `ALLOWED_ORIGINS` in config; only listed origins can make cross-origin requests |
| Google token verification | Server-side `id_token.verify_oauth2_token()` — client cannot forge a login |
| Gmail scope | Narrowest possible: `gmail.send` only — Kaikoo cannot read the user's inbox |
| Secrets | Never committed to git; managed via `.env` locally and platform dashboards in production |

---

## 10. Deployment Architecture

```
  Vercel (CDN + Edge)                Railway
  ┌─────────────────────┐            ┌──────────────────────┐
  │  frontend/dist/     │            │  FastAPI (uvicorn)   │
  │  ─ static files     │   HTTPS    │  app.main:app        │
  │  ─ vercel.json SPA  │ ─────────► │  0.0.0.0:$PORT       │
  │    rewrite rule     │            └────────┬─────────────┘
  └─────────────────────┘                     │ asyncpg
                                              ▼
                                    ┌──────────────────────┐
                                    │  PostgreSQL (Railway │
                                    │  managed plugin)     │
                                    └──────────────────────┘
```

### Environment separation

| Variable | Development | Production |
|---|---|---|
| `DATABASE_URL` | `localhost:5432/kaikoo` | Railway internal URL |
| `ALLOWED_ORIGINS` | `http://localhost:5173` | `https://kaikoo.vercel.app` |
| Redirect URIs | `http://localhost:8000/api/v1/...` | `https://<railway-domain>/api/v1/...` |
| `ENVIRONMENT` | `development` (SQL echo on) | `production` (SQL echo off) |

---

## 11. Key Design Decisions

### Single Claude call per note
Rather than making separate calls for (1) categorisation, (2) continuation detection, and (3) intent extraction, all three are handled in one structured-JSON response. This keeps the note-save latency to a single round-trip to Anthropic (~300–500 ms with Haiku) instead of 1–1.5 s.

### No real-time WebSocket
The app is read-heavy and single-user. TanStack Query's `staleTime: 30s` with query invalidation on mutations provides a fast, consistent experience without the complexity of WebSocket connections.

### Flat notes + AI categories
There are no manual folders. Every note is created flat and Claude decides where it belongs. This eliminates the friction of choosing a folder before writing. Users who want to search by topic can filter by category via the sidebar.

### Append-to logic
When Claude determines a new note is a continuation of an existing one, the new text is appended to the existing note record (separated by a blank line). This means related thoughts surface as a single coherent note rather than fragmented entries — better for reading and summarising.

### Token encryption
Google and Notion OAuth tokens are long-lived credentials. Storing them in plaintext in the database would be a significant security risk if the DB were ever exposed. Fernet encryption means the tokens are useless without the `FERNET_KEY` environment variable.

### Gmail scope scoping
Only `gmail.send` is requested — not `gmail.readonly` or `gmail.modify`. Kaikoo genuinely only needs to send emails; requesting broader scopes would be unnecessary, would make the OAuth consent screen more alarming, and would increase risk surface.

### Notion sync is best-effort
Notion's API is relatively slow (~500 ms). By making the sync happen after the DB commit and swallowing errors silently, the note-save response time is not affected by Notion outages. Users whose Notion integration is broken will still have all their notes in the Kaikoo database.
