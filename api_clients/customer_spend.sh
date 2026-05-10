#!/usr/bin/env bash
set -euo pipefail

API_BASE_URL="${API_BASE_URL:-http://127.0.0.1:8000}"

curl --silent --show-error \
  "${API_BASE_URL}/customers/spend"
echo
