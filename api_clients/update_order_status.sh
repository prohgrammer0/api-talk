#!/usr/bin/env bash
set -euo pipefail

API_BASE_URL="${API_BASE_URL:-http://127.0.0.1:8000}"
ORDER_ID="${1:-1001}"
STATUS="${2:-shipped}"

curl --silent --show-error \
  --request PATCH \
  --header "Content-Type: application/json" \
  --data "{\"status\": \"${STATUS}\"}" \
  "${API_BASE_URL}/orders/${ORDER_ID}/status"
echo
