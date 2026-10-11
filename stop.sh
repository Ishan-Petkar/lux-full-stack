#!/usr/bin/env bash
# Stop the AI-Based Product Recommendation System.
#
#   ./stop.sh                 stop the app and the MongoDB container (database volume is KEPT)
#   ./stop.sh --purge         ...and DELETE the MongoDB data volume (asks to confirm)
#   ./stop.sh --purge --yes   same, without the prompt
#   ./stop.sh --stop-docker   ...and also stop the colima Docker VM (only if no other containers are running)
#   ./stop.sh --port 8600     if you started the app on a non-default port
set -uo pipefail
cd "$(dirname "$0")"
ROOT="$(pwd)"
RUN="$ROOT/.run"; PIDFILE="$RUN/streamlit.pid"; MARK="$RUN/colima_started_by_script"
PORT=8501; PURGE=0; YES=0; STOP_DOCKER=0; CONTAINER=product_reco_mongo
while [ $# -gt 0 ]; do
  case "$1" in
    --purge) PURGE=1 ;; --yes|-y) YES=1 ;; --stop-docker) STOP_DOCKER=1 ;;
    --port) shift; PORT="${1:-}" ;;
    -h|--help) sed -n '2,9p' "$0"; exit 0 ;;
    *) echo "Unknown option: $1 (see --help)"; exit 2 ;;
  esac; shift
done
if [ -t 1 ]; then G=$'\033[32m'; R=$'\033[31m'; Y=$'\033[33m'; B=$'\033[1m'; N=$'\033[0m'; else G=; R=; Y=; B=; N=; fi
ok() { echo "  ${G}✔${N} $*"; }; warn() { echo "  ${Y}!${N} $*"; }; step() { echo "${B}$*${N}"; }
alive() { [ -n "${1:-}" ] && kill -0 "$1" 2>/dev/null; }
STATUS=0
echo "${B}AI-Based Product Recommendation System — stop${N}"; echo

# ---------------------------------------------------------------- app
step "[1] Streamlit app"
PID=""; [ -f "$PIDFILE" ] && PID="$(cat "$PIDFILE" 2>/dev/null)"
if alive "$PID"; then
  # only kill it if it really is our streamlit process (guards against a recycled pid)
  if ps -p "$PID" -o command= 2>/dev/null | grep -q "streamlit.* run app.py"; then
    kill "$PID" 2>/dev/null
    for _ in $(seq 1 20); do alive "$PID" || break; sleep 0.5; done
    if alive "$PID"; then kill -9 "$PID" 2>/dev/null; sleep 0.5; fi
    alive "$PID" && { echo "  ${R}✘ could not stop pid $PID${N}"; STATUS=1; } || ok "stopped app (pid $PID)"
  else
    warn "pid $PID is not our streamlit process — left alone"; 
  fi
else
  ok "app was not running (no live pid file)"
fi
rm -f "$PIDFILE"
# a leftover streamlit of THIS project on the port (e.g. started by hand)?
LEFT="$(lsof -nP -tiTCP:"$PORT" -sTCP:LISTEN 2>/dev/null | head -1)"
if [ -n "$LEFT" ]; then
  if ps -p "$LEFT" -o command= 2>/dev/null | grep -q "streamlit.* run app.py"; then
    kill "$LEFT" 2>/dev/null; sleep 1; ok "also stopped a manually started streamlit on port $PORT (pid $LEFT)"
  else warn "port $PORT is used by another program (pid $LEFT) — not ours, left alone"; fi
fi

# ---------------------------------------------------------------- mongo
step "[2] MongoDB container"
if ! command -v docker >/dev/null 2>&1 || ! docker info >/dev/null 2>&1; then
  ok "Docker not running — nothing to stop"
else
  if [ "$PURGE" = 1 ]; then
    if [ "$YES" = 0 ]; then
      printf "  ${Y}This permanently deletes ALL MongoDB data for this project (volume mongo_data). Type 'delete' to confirm: ${N}"
      read -r ANS
      [ "$ANS" = delete ] || { echo "  purge cancelled — stopping without deleting data"; PURGE=0; }
    fi
  fi
  if [ "$PURGE" = 1 ]; then
    docker compose down -v >"$RUN/compose.log" 2>&1 && ok "container removed and data volume DELETED" || { echo "  ${R}✘ docker compose down -v failed (see $RUN/compose.log)${N}"; STATUS=1; }
  else
    docker compose down >"$RUN/compose.log" 2>&1 && ok "container stopped and removed (data volume kept — next ./start.sh reuses it)" || { echo "  ${R}✘ docker compose down failed (see $RUN/compose.log)${N}"; STATUS=1; }
  fi
fi

# ---------------------------------------------------------------- docker vm
step "[3] Docker VM (colima)"
if [ "$STOP_DOCKER" = 1 ] || [ -f "$MARK" ]; then
  if command -v colima >/dev/null 2>&1 && colima status >/dev/null 2>&1; then
    OTHERS="$(docker ps -q 2>/dev/null | wc -l | tr -d ' ')"
    if [ "$OTHERS" != 0 ]; then warn "$OTHERS other container(s) still running — colima left running"
    else colima stop >"$RUN/colima.log" 2>&1 && { ok "colima stopped"; rm -f "$MARK"; } || { echo "  ${R}✘ colima stop failed${N}"; STATUS=1; }; fi
  else ok "colima not running"; rm -f "$MARK"; fi
else
  ok "left running (started outside this script; use --stop-docker to stop it)"
fi

# ---------------------------------------------------------------- verify
step "[4] Verification"
lsof -nP -iTCP:"$PORT" -sTCP:LISTEN >/dev/null 2>&1 && { warn "something still listens on $PORT"; } || ok "port $PORT is free"
if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
  docker ps --format '{{.Names}}' | grep -qx "$CONTAINER" && { echo "  ${R}✘ $CONTAINER still running${N}"; STATUS=1; } || ok "$CONTAINER is not running"
fi
echo
[ "$STATUS" = 0 ] && echo "${G}${B}Stopped.${N}" || echo "${R}${B}Stopped with problems — see above.${N}"
exit "$STATUS"
