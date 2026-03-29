#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

PORT="${PORT:-8000}"
BASE_URL="http://127.0.0.1:${PORT}"

cleanup() {
  if [[ -n "${SERVER_PID:-}" ]] && kill -0 "$SERVER_PID" 2>/dev/null; then
    kill "$SERVER_PID" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

python3 app.py > /tmp/ai_ads_server.log 2>&1 &
SERVER_PID=$!

echo "Started server PID=${SERVER_PID} on ${BASE_URL}"

for _ in {1..30}; do
  if curl -fsS "${BASE_URL}/health" >/dev/null 2>&1; then
    break
  fi
  sleep 0.25
done

echo "\n[1/4] Health check"
curl -fsS "${BASE_URL}/health" | python3 -m json.tool

echo "\n[2/4] Create sample ad"
curl -fsS -X POST "${BASE_URL}/ads" \
  -H 'Content-Type: application/json' \
  -d '{
    "title":"Weekend 40% Off Sneakers",
    "description":"Running shoes discount this weekend",
    "category":"shoes",
    "owner_name":"Downtown Sports",
    "city":"Austin",
    "price":120,
    "discount_percent":40,
    "source_url":"https://shop.example/sneakers",
    "ad_type":"business"
  }' | python3 -m json.tool

echo "\n[3/4] List ads"
curl -fsS "${BASE_URL}/ads" | python3 -m json.tool

echo "\n[4/4] Search offers"
curl -fsS -X POST "${BASE_URL}/search" \
  -H 'Content-Type: application/json' \
  -d '{
    "query":"running shoes discounts",
    "city":"Austin",
    "budget":150,
    "limit":5
  }' | python3 -m json.tool

echo "\nLive test completed successfully."
