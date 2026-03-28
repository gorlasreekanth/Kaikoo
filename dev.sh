#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# dev.sh — one-command local dev setup for Kaikoo
# Starts PostgreSQL, creates the DB, runs migrations, then boots
# the FastAPI backend and Vite frontend in parallel.
# ---------------------------------------------------------------------------
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ── Colour helpers ──────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
info()    { echo -e "${CYAN}[kaikoo]${NC} $*"; }
success() { echo -e "${GREEN}[kaikoo]${NC} $*"; }
warn()    { echo -e "${YELLOW}[kaikoo]${NC} $*"; }
error()   { echo -e "${RED}[kaikoo]${NC} $*" >&2; exit 1; }

# ── PATH: make sure Homebrew bins are available ─────────────────────────────
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"

# ── 1. Check .env files exist ───────────────────────────────────────────────
if [ ! -f "$SCRIPT_DIR/backend/.env" ]; then
  warn "backend/.env not found — copying from backend/.env.example"
  cp "$SCRIPT_DIR/backend/.env.example" "$SCRIPT_DIR/backend/.env"
  warn "Edit backend/.env and fill in your keys, then re-run this script."
  exit 1
fi

if [ ! -f "$SCRIPT_DIR/frontend/.env" ]; then
  warn "frontend/.env not found — copying from frontend/.env.example"
  cp "$SCRIPT_DIR/frontend/.env.example" "$SCRIPT_DIR/frontend/.env"
fi

# ── 2. Read DATABASE_URL from backend/.env ──────────────────────────────────
DB_URL=$(grep '^DATABASE_URL=' "$SCRIPT_DIR/backend/.env" | cut -d= -f2- | tr -d '"'"'" | sed 's|postgresql+asyncpg://||')
# DB_URL is now:  user:password@host:port/dbname
DB_USER=$(echo "$DB_URL" | sed 's/:.*@.*//')
DB_PASS=$(echo "$DB_URL" | sed 's/[^:]*:\(.*\)@.*/\1/')
DB_HOST=$(echo "$DB_URL" | sed 's/.*@\(.*\):.*/\1/')
DB_PORT=$(echo "$DB_URL" | sed 's/.*:\([0-9]*\)\/.*/\1/')
DB_NAME=$(echo "$DB_URL" | sed 's/.*\///')

info "Database: ${DB_NAME} @ ${DB_HOST}:${DB_PORT} (user: ${DB_USER})"

# ── 3. Start PostgreSQL if not running ─────────────────────────────────────
PG_DATA="/opt/homebrew/var/postgresql@14"
if ! pg_ctl status -D "$PG_DATA" &>/dev/null; then
  info "Starting PostgreSQL..."
  pg_ctl start -D "$PG_DATA" -l "$PG_DATA/postgresql.log" -w
  sleep 1
  success "PostgreSQL started."
else
  success "PostgreSQL already running."
fi

# ── 4. Create DB and user if they don't exist ───────────────────────────────
PSQL="psql -h $DB_HOST -p $DB_PORT"

# Create user if missing
if ! $PSQL -U postgres -tAc "SELECT 1 FROM pg_roles WHERE rolname='$DB_USER'" | grep -q 1; then
  info "Creating database user '${DB_USER}'..."
  $PSQL -U postgres -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASS';" || true
fi

# Create database if missing
if ! $PSQL -U postgres -tAc "SELECT 1 FROM pg_database WHERE datname='$DB_NAME'" | grep -q 1; then
  info "Creating database '${DB_NAME}'..."
  $PSQL -U postgres -c "CREATE DATABASE $DB_NAME OWNER $DB_USER;"
  success "Database '${DB_NAME}' created."
else
  success "Database '${DB_NAME}' already exists."
fi

# Grant privileges
$PSQL -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;" &>/dev/null || true

# ── 5. Python virtualenv + dependencies ─────────────────────────────────────
cd "$SCRIPT_DIR/backend"

if [ ! -d "venv" ]; then
  info "Creating Python virtual environment..."
  python3 -m venv venv
fi

info "Installing/updating Python dependencies..."
./venv/bin/pip install -q -r requirements.txt

# ── 6. Run Alembic migrations ───────────────────────────────────────────────
info "Running database migrations..."
./venv/bin/alembic upgrade head
success "Migrations complete."

# ── 7. Frontend dependencies ─────────────────────────────────────────────────
cd "$SCRIPT_DIR/frontend"
if [ ! -d "node_modules" ]; then
  info "Installing frontend dependencies..."
  npm install
fi

# ── 8. Launch backend + frontend in parallel ────────────────────────────────
cd "$SCRIPT_DIR"
success "Starting backend (port 8000) and frontend (port 5173)..."
echo ""

trap 'echo ""; info "Shutting down..."; kill 0' SIGINT SIGTERM

# Start backend
(
  cd "$SCRIPT_DIR/backend"
  source venv/bin/activate
  uvicorn app.main:app --reload --port 8000 2>&1 | sed 's/^/\033[0;35m[backend]\033[0m /'
) &

# Start frontend
(
  cd "$SCRIPT_DIR/frontend"
  npm run dev 2>&1 | sed 's/^/\033[0;36m[frontend]\033[0m /'
) &

wait
