#!/usr/bin/env bash
set -euo pipefail
cd /home/sirobo/bpkr
export PATH="/home/sirobo/.nvm/versions/node/v22.22.2/bin:$PATH"
export PIP_CACHE_DIR="/home/sirobo/bpkr/.pip-cache"
export npm_config_cache="/home/sirobo/bpkr/.npm-cache"
export XDG_CACHE_HOME="/home/sirobo/bpkr/.cache"
if [[ -f .env ]]; then
  set -a
  source .env
  set +a
fi
: "${BPKR_SECRET:?Set BPKR_SECRET di file .env}"
: "${DATABASE_URL:?Set DATABASE_URL di file .env}"
case "${1:-start}" in
  setup)
    python3 -m venv .venv
    .venv/bin/pip install -r backend/requirements.txt
    ( cd frontend && npm install && npm run build )
    PYTHONPATH=backend .venv/bin/python backend/seed.py
    ;;
  start)
    exec .venv/bin/uvicorn app:app --app-dir backend --host "${BPKR_HOST:-127.0.0.1}" --port "${BPKR_PORT:-9787}" --proxy-headers --forwarded-allow-ips 127.0.0.1
    ;;
  build)
    (cd frontend && npm run build)
    ;;
  seed)
    PYTHONPATH=backend .venv/bin/python backend/seed.py
    ;;
  test)
    PYTHONPATH=backend .venv/bin/python -m compileall backend -q
    ;;
  *)
    echo "Gunakan: ./server.sh [setup|start|build|seed|test]" >&2
    exit 2
    ;;
esac
