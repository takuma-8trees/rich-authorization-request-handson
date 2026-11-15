#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
trap 'docker compose start opa >/dev/null' EXIT
docker compose stop opa
docker compose run --rm --no-deps -e OPA_OFFLINE=1 -v "$PWD/tests:/app/tests:ro" api python /app/tests/smoke.py
docker compose start opa
trap - EXIT
