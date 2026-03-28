#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# dev.sh — one-command local dev for Kaikoo
# Usage: npm run dev   OR   bash dev.sh
# ---------------------------------------------------------------------------
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
info()    { echo -e "${CYAN}[kaikoo]${NC} $*"; }
success() { echo -e "${GREEN}[kaikoo]${NC} $*"; }
warn()    { echo -e "${YELLOW}[kaikoo]${NC} $*"; }

# ── 1. Root .env (docker-compose vars) ─────────────────────────────────────
if [ ! -f ".env" ]; then
  cp .env.example .env
  success "Created .env from .env.example"
fi

# ── 2. Backend .env (API keys + secrets) ───────────────────────────────────
if [ ! -f "backend/.env" ]; then
  cp backend/.env.example backend/.env
  echo ""
  warn "backend/.env was just created. Fill in your secrets before continuing:"
  warn "  SECRET_KEY, FERNET_KEY, ANTHROPIC_API_KEY, GOOGLE_CLIENT_ID, etc."
  warn "  Then run: npm run dev"
  echo ""
  exit 1
fi

# ── 3. Start everything ─────────────────────────────────────────────────────
info "Starting Kaikoo (postgres + backend + frontend)..."
echo ""
docker compose up --build
