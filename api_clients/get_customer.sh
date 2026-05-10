#!/usr/bin/env bash
set -euo pipefail

API_BASE_URL="${API_BASE_URL:-http://127.0.0.1:8000}"
CUSTOMER_ID="${1:-1}"

curl --silent --show-error \
  "${API_BASE_URL}/customers/${CUSTOMER_ID}"
echo
