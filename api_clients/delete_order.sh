#!/usr/bin/env bash
set -euo pipefail

API_BASE_URL="${API_BASE_URL:-http://127.0.0.1:8000}"
ORDER_ID="${1:-1004}"

curl --silent --show-error \
  --request DELETE \
  --write-out "Deleted order ${ORDER_ID}. HTTP %{http_code}\n" \
  --output /dev/null \
  "${API_BASE_URL}/orders/${ORDER_ID}"
