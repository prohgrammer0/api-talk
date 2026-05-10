#!/usr/bin/env bash
set -euo pipefail

API_BASE_URL="${API_BASE_URL:-http://127.0.0.1:8000}"

curl --silent --show-error \
  --request POST \
  --header "Content-Type: application/json" \
  --data '{
    "customer_id": 2,
    "order_date": "2026-05-06",
    "status": "open",
    "items": [
      {
        "product_name": "API Integration Workshop",
        "quantity": 1,
        "unit_price": 1200.0
      },
      {
        "product_name": "Support Retainer",
        "quantity": 2,
        "unit_price": 350.0
      }
    ]
  }' \
  "${API_BASE_URL}/orders"
echo
