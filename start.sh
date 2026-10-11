#!/usr/bin/env bash
# Start the AI-Based Product Recommendation System on http://localhost:<port>
#
#   ./start.sh              verify prerequisites, start MongoDB (docker compose) + the app
#   ./start.sh --check      only verify prerequisites; change nothing
#   ./start.sh --mock       skip Docker/MongoDB and use the in-memory fallback database
#   ./start.sh --port 8600  use another app port (default 8501)
#   ./start.sh --no-open    do not open the browser
#
# Stop with ./stop.sh.  Exit code 0 = running, non-zero = a prerequisite failed (message says which).
set -uo pipefail
cd "$(dirname "$0")"
ROOT="$(pwd)"
RUN="$ROOT/.run"; PIDFILE="$RUN/streamlit.pid"; LOG="$RUN/streamlit.log"; MARK="$RUN/colima_started_by_script"
PORT=8501; MONGO_PORT=27017; CHECK_ONLY=0; MOCK=0; OPEN=1
CONTAINER=product_reco_mongo

while [ $# -gt 0 ]; do
  case "$1" in
    --check) CHECK_ONLY=1 ;; --mock) MOCK=1 ;; --no-open) OPEN=0 ;;
    --port) shift; PORT="${1:-}" ;;
    -h|--help) sed -n '2,12p' "$0"; exit 0 ;;
    *) echo "Unknown option: $1 (see --help)"; exit 2 ;;
  esac; shift
done
case "$PORT" in ''|*[!0-9]*) echo "Invalid --port"; exit 2 ;; esac

if [ -t 1 ]; then G=$'\033[32m'; R=$'\033[31m'; Y=$'\033[33m'; B=$'\033[1m'; N=$'\033[0m'; else G=; R=; Y=; B=; N=; fi
STEP=0
ok()   { echo "  ${G}✔${N} $*"; }
warn() { echo "  ${Y}!${N} $*"; }
fail() { echo "  ${R}✘ $1${N}"; shift; for l in "$@"; do echo "      $l"; done; echo; echo "${R}Not started.${N} Fix the point above and re-run ./start.sh"; exit 1; }
step() { STEP=$((STEP+1)); echo "${B}[$STEP] $*${N}"; }
listening() { lsof -nP -iTCP:"$1" -sTCP:LISTEN >/dev/null 2>&1; }
alive() { [ -n "${1:-}" ] && kill -0 "$1" 2>/dev/null; }

echo "${B}AI-Based Product Recommendation System — start${N}"
[ "$CHECK_ONLY" = 1 ] && echo "(check only: nothing will be changed)"
echo

# ---------------------------------------------------------------- 1. project files
step "Project files"
for f in app.py requirements.txt docker-compose.yml shop/__init__.py shop/db.py shop/recommender.py shop/seed_data.py; do
  [ -f "$f" ] || fail "Missing project file: $f" "Run this script from the project folder: $ROOT"
done
ok "all required files present"

# ---------------------------------------------------------------- 2. already running?
step "Already running?"
if [ -f "$PIDFILE" ] && alive "$(cat "$PIDFILE" 2>/dev/null)"; then
  ok "app already running (pid $(cat "$PIDFILE")) → http://localhost:$PORT"
  [ "$CHECK_ONLY" = 1 ] || { echo; echo "${G}${B}Already up.${N} Use ./stop.sh to stop it."; }
  exit 0
fi
rm -f "$PIDFILE"
ok "not running"

# ---------------------------------------------------------------- 3. python
step "Python 3.10+"
PY=""
for c in python3 python; do
  if command -v "$c" >/dev/null 2>&1 && "$c" -c 'import sys; sys.exit(0 if sys.version_info>=(3,10) else 1)' 2>/dev/null; then PY="$c"; break; fi
done
[ -n "$PY" ] || fail "Python 3.10 or newer not found" "Install it (macOS: brew install python) and re-run."
ok "$($PY --version 2>&1) ($(command -v $PY))"

# ---------------------------------------------------------------- 4. venv + packages
step "Virtual environment and packages"
VPY="$ROOT/.venv/bin/python"
IMPORTS='import streamlit, pymongo, pandas, sklearn, mongomock, PIL'
if [ ! -x "$VPY" ]; then
  if [ "$CHECK_ONLY" = 1 ]; then warn ".venv missing — ./start.sh would create it"
  else
    echo "      creating .venv ..."; "$PY" -m venv .venv >/dev/null 2>&1 || fail "Could not create .venv" "Try: $PY -m venv .venv"
    ok ".venv created"
  fi
fi
if [ -x "$VPY" ]; then
  if "$VPY" -c "$IMPORTS" 2>/dev/null; then ok "required packages installed"
  elif [ "$CHECK_ONLY" = 1 ]; then warn "packages missing — ./start.sh would run: pip install -r requirements.txt"
  else
    echo "      installing requirements.txt (first run can take a minute) ..."
    "$VPY" -m pip install -q --disable-pip-version-check -r requirements.txt >"$RUN/pip.log" 2>&1 \
      || fail "pip install failed" "See $RUN/pip.log"
    "$VPY" -c "$IMPORTS" 2>/dev/null || fail "Packages still not importable after install" "See $RUN/pip.log"
    ok "packages installed"
  fi
fi

# ---------------------------------------------------------------- 5. ports
step "Network ports"
if listening "$PORT"; then
  fail "App port $PORT is already in use by another program" "$(lsof -nP -iTCP:$PORT -sTCP:LISTEN | sed -n '2p')" "Free it or choose another port: ./start.sh --port 8600"
fi
ok "app port $PORT is free"
if [ "$MOCK" = 0 ]; then
  if listening "$MONGO_PORT"; then
    if docker ps --format '{{.Names}}' 2>/dev/null | grep -qx "$CONTAINER"; then ok "MongoDB port $MONGO_PORT held by our container ($CONTAINER)"
    else fail "MongoDB port $MONGO_PORT is in use by something other than $CONTAINER" "$(lsof -nP -iTCP:$MONGO_PORT -sTCP:LISTEN | sed -n '2p')" "Stop that service, or run with --mock for the in-memory database."; fi
  else ok "MongoDB port $MONGO_PORT is free"; fi
fi

# ---------------------------------------------------------------- 6. docker / mongodb
if [ "$MOCK" = 1 ]; then
  step "MongoDB"; warn "--mock: using the in-memory mongomock database (data resets on restart)"
else
  step "Docker"
  command -v docker >/dev/null 2>&1 || fail "Docker CLI not found" "Install Docker Desktop, or: brew install docker docker-compose colima"
  ok "docker CLI found"
  docker compose version >/dev/null 2>&1 || fail "'docker compose' plugin not found" "Install it: brew install docker-compose"
  ok "docker compose available"
  if ! docker info >/dev/null 2>&1; then
    if command -v colima >/dev/null 2>&1; then
      if [ "$CHECK_ONLY" = 1 ]; then warn "Docker daemon not running — ./start.sh would run 'colima start'"
      else
        echo "      Docker daemon is down; starting colima (first boot can take a minute) ..."
        colima start >"$RUN/colima.log" 2>&1 || fail "colima failed to start" "See $RUN/colima.log"
        touch "$MARK"
        docker info >/dev/null 2>&1 || fail "Docker daemon still unreachable after colima start" "See $RUN/colima.log"
        ok "colima started"
      fi
    else
      fail "Docker daemon is not running" "Start Docker Desktop (or install colima) and re-run, or use ./start.sh --mock"
    fi
  else ok "Docker daemon reachable"; fi

  if [ "$CHECK_ONLY" = 0 ]; then
    step "MongoDB container ($CONTAINER)"
    docker compose up -d >"$RUN/compose.log" 2>&1 || fail "docker compose up failed" "$(tail -5 "$RUN/compose.log")"
    printf "      waiting for MongoDB to become healthy "
    HEALTH=""
    for _ in $(seq 1 40); do
      HEALTH="$(docker inspect -f '{{.State.Health.Status}}' "$CONTAINER" 2>/dev/null || echo none)"
      [ "$HEALTH" = healthy ] && break; printf "."; sleep 2
    done; echo
    [ "$HEALTH" = healthy ] || fail "MongoDB did not become healthy (status: $HEALTH)" "docker logs $CONTAINER"
    ok "MongoDB is healthy on localhost:$MONGO_PORT"

    step "Database connection and seed data"
    OUT="$(USE_MOCK_DB=false "$VPY" - <<'PYEOF' 2>&1
from shop.db import connect
from shop.seed_data import seed_if_empty
db, backend = connect()
seeded = seed_if_empty(db)
print(f"{backend}|{db.name}|{db.products.count_documents({})}|{'seeded now' if seeded else 'already seeded'}")
PYEOF
)" || fail "Could not connect to MongoDB from Python" "$OUT"
    IFS='|' read -r BK DBN CNT SEED <<<"$OUT"
    [ "$BK" = "MongoDB" ] || fail "Connected to '$BK' instead of a real MongoDB" "$OUT"
    ok "$BK database '$DBN': $CNT products ($SEED)"
  fi
fi

if [ "$CHECK_ONLY" = 1 ]; then echo; echo "${G}${B}All checks done.${N} Run ./start.sh to start."; exit 0; fi

# ---------------------------------------------------------------- 7. start the app
step "Starting the app"
mkdir -p "$RUN"; : >"$LOG"
if [ "$MOCK" = 1 ]; then export USE_MOCK_DB=true; else export USE_MOCK_DB=false; fi
nohup "$ROOT/.venv/bin/streamlit" run app.py --server.port "$PORT" --server.address localhost \
      --server.headless true --browser.gatherUsageStats false >"$LOG" 2>&1 &
APP_PID=$!; echo "$APP_PID" >"$PIDFILE"
printf "      waiting for http://localhost:$PORT "
UP=0
for _ in $(seq 1 45); do
  alive "$APP_PID" || break
  if [ "$(curl -s -o /dev/null -w '%{http_code}' "http://localhost:$PORT/_stcore/health" 2>/dev/null)" = 200 ]; then UP=1; break; fi
  printf "."; sleep 1
done; echo
if [ "$UP" != 1 ]; then
  alive "$APP_PID" && kill "$APP_PID" 2>/dev/null; rm -f "$PIDFILE"
  fail "The app did not come up" "Last log lines ($LOG):" "$(tail -8 "$LOG")"
fi
ok "app is serving (pid $APP_PID)"

echo
echo "${G}${B}Running →  http://localhost:$PORT${N}"
echo "  database : $([ "$MOCK" = 1 ] && echo 'in-memory mongomock' || echo "MongoDB 7 in Docker (container $CONTAINER, volume mongo_data)")"
echo "  log      : $LOG"
echo "  stop     : ./stop.sh"
[ "$OPEN" = 1 ] && command -v open >/dev/null 2>&1 && open "http://localhost:$PORT" >/dev/null 2>&1
exit 0
