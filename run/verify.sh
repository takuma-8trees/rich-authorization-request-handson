#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
for url in http://localhost:18770/health http://localhost:18771/realms/rar-lab/.well-known/openid-configuration; do
 n=0
 until curl -fsS --max-time 3 "$url" >/dev/null 2>&1; do
  n=$((n+1)); if [ "$n" -ge 120 ]; then echo "Not ready: $url" >&2; exit 1; fi
  sleep 1
 done
done
docker compose run --rm --no-deps opa test /policies
docker compose run --rm --no-deps -v "$PWD/tests:/app/tests:ro" api python -m tests.security_checks
docker compose run --rm --no-deps -v "$PWD/tests:/app/tests:ro" api python /app/tests/smoke.py
