# Kaikoo

A minimalist personal assistant web app that captures your thoughts, auto-organises them with AI, and takes action — creating calendar events, drafting emails, and syncing to Notion — all from a single note input.

---

## Features

| Feature | Description |
|---|---|
| **Text & voice input** | Type notes or dictate them using the browser's Web Speech API |
| **AI categorisation** | Claude reads each note, picks the right category, and appends to an existing note if it's a continuation |
| **Intent detection** | Meeting/reminder and email intents are detected automatically; a confirmation modal lets you review before anything is sent |
| **Summaries** | Request a Claude-generated prose summary of any category |
| **Google Calendar** | Confirm a detected event and it's created in your primary calendar |
| **Gmail** | Review and send (or save as draft) emails generated from your notes |
| **Notion** | Notes are synced to Notion pages organised by category |
| **Dark UI** | Minimalist dark theme, accent `#7c6af7` |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 19, Vite, TypeScript, Tailwind CSS v4 |
| State / data | Zustand (auth), TanStack Query (server state) |
| Backend | Python 3.12+, FastAPI, SQLAlchemy (async) |
| Database | PostgreSQL 15+ |
| Migrations | Alembic |
| AI | Anthropic Claude (`claude-haiku-4-5` for notes, `claude-sonnet-4-6` for summaries) |
| Auth | Google OAuth 2.0 (ID token → backend JWT) |
| Speech | Web Speech API (browser-native, no API key) |
| Integrations | Google Calendar API, Gmail API, Notion API |
| Deploy | Vercel (frontend), Railway (backend + PostgreSQL) |

---

## Repository Layout

```
Kaikoo/
├── frontend/          React + Vite web app
│   ├── src/
│   │   ├── api/       Axios client + typed endpoint helpers
│   │   ├── components/  UI, layout, notes, confirmation modals, integrations
│   │   ├── hooks/     useNotes, useCategories, useVoiceInput
│   │   ├── pages/     Dashboard, Category, Summary, Settings, Login
│   │   ├── router/    React Router v7 + protected route guard
│   │   ├── store/     Zustand auth store (persisted)
│   │   └── utils/     cn(), formatDate, constants
│   └── vercel.json    SPA rewrite rule
│
├── backend/           FastAPI Python app
│   ├── app/
│   │   ├── models/    SQLAlchemy ORM models (User, Category, Note, Integration)
│   │   ├── schemas/   Pydantic request/response shapes
│   │   ├── routers/   auth, notes, categories, summaries, calendar, gmail, notion, integrations
│   │   ├── services/  claude, auth, calendar, gmail, notion
│   │   └── utils/     Fernet token encryption
│   ├── alembic/       Migration scripts
│   ├── scripts/       Key generation helper
│   ├── Procfile       Railway start command
│   └── railway.json   Railway deploy config
│
├── ARCHITECTURE.md    System design and data-flow documentation
├── SETUP.md           Step-by-step local and production setup guide
└── README.md          This file
```

---

## Quick Start

See [SETUP.md](./SETUP.md) for the full guide. The short version:

```bash
# 1. Clone
git clone https://github.com/gorlasreekanth/Kaikoo.git && cd Kaikoo

# 2. Backend
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python scripts/generate_keys.py   # paste output into .env
cp .env.example .env              # then fill in all API keys
alembic upgrade head
uvicorn app.main:app --reload     # http://localhost:8000

# 3. Frontend (new terminal)
cd ../frontend
npm install
cp .env.example .env              # set VITE_GOOGLE_CLIENT_ID
npm run dev                       # http://localhost:5173
```

---

## Documentation

- [SETUP.md](./SETUP.md) — prerequisites, environment variables, OAuth console configuration, running locally, deploying to Vercel + Railway
- [ARCHITECTURE.md](./ARCHITECTURE.md) — system design, AI pipeline, database schema, component tree, security model

---

## License

MIT
