#!/usr/bin/env bash
set -euo pipefail

API_BASE_URL="${API_BASE_URL:-http://127.0.0.1:8000}"
ORDER_ID="${1:-}"

if [[ -n "${ORDER_ID}" ]]; then
  curl --silent --show-error \
    "${API_BASE_URL}/order-items?order_id=${ORDER_ID}"
else
  curl --silent --show-error \
    "${API_BASE_URL}/order-items"
fi
echo
