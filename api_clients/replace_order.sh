#!/usr/bin/env bash
set -euo pipefail

API_BASE_URL="${API_BASE_URL:-http://127.0.0.1:8000}"
ORDER_ID="${1:-1003}"

curl --silent --show-error \
  --request PUT \
  --header "Content-Type: application/json" \
  --data '{
    "customer_id": 1,
    "order_date": "2026-05-07",
    "status": "open",
    "items": [
      {
        "product_name": "Revised Analytics Dashboard License",
        "quantity": 3,
        "unit_price": 500.0
      },
      {
        "product_name": "Implementation Support",
        "quantity": 2,
        "unit_price": 280.5
      }
    ]
  }' \
  "${API_BASE_URL}/orders/${ORDER_ID}"
echo
