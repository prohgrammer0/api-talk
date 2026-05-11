# Orders API

A small FastAPI and SQLite project for working with customers, orders, and order
items. The project includes:

- A seeded SQLite database.
- Direct Python scripts that run SQL against the database.
- A FastAPI app exposing the same operations over HTTP.
- Curl-based API client scripts.
- A simple HTMX browser UI.

## Requirements

- Python 3.11 or newer

Install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Database

The SQLite database lives at:

```text
data/orders.db
```

Seed or reset the database:

```bash
python scripts/setup_data.py
```

The database is built from:

- `data/schema.sql`
- `data/seed.sql`

Tables:

- `customers`
- `orders`
- `order_items`

## Run the API

Start the FastAPI server:

```bash
python -m uvicorn api_talk.api:app --reload
```

Open the generated FastAPI docs:

```text
http://127.0.0.1:8000/docs
```

Open the simple browser UI:

```text
http://127.0.0.1:8000/ui
```

## API Endpoints

### Customers

List customers:

```bash
curl http://127.0.0.1:8000/customers
```

Get one customer:

```bash
curl http://127.0.0.1:8000/customers/1
```

Get customer spend totals, excluding cancelled orders:

```bash
curl http://127.0.0.1:8000/customers/spend
```

### Orders

List orders:

```bash
curl http://127.0.0.1:8000/orders
```

List orders by status:

```bash
curl "http://127.0.0.1:8000/orders?status=open"
```

Allowed statuses:

- `open`
- `shipped`
- `cancelled`

Get one order:

```bash
curl http://127.0.0.1:8000/orders/1001
```

Create an order:

```bash
curl -X POST http://127.0.0.1:8000/orders \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": 2,
    "order_date": "2026-05-06",
    "status": "open",
    "items": [
      {
        "product_name": "API Integration Workshop",
        "quantity": 1,
        "unit_price": 1200.0
      }
    ]
  }'
```

Replace an order:

```bash
curl -X PUT http://127.0.0.1:8000/orders/1001 \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": 1,
    "order_date": "2026-05-07",
    "status": "open",
    "items": [
      {
        "product_name": "Revised Analytics Dashboard License",
        "quantity": 3,
        "unit_price": 500.0
      }
    ]
  }'
```

Update an order status:

```bash
curl -X PATCH http://127.0.0.1:8000/orders/1001/status \
  -H "Content-Type: application/json" \
  -d '{"status": "shipped"}'
```

Delete an order:

```bash
curl -X DELETE http://127.0.0.1:8000/orders/1004
```

### Order Items

List all order items:

```bash
curl http://127.0.0.1:8000/order-items
```

List order items for one order:

```bash
curl "http://127.0.0.1:8000/order-items?order_id=1001"
```

Get one order item:

```bash
curl http://127.0.0.1:8000/order-items/1
```

Get one order with its items:

```bash
curl http://127.0.0.1:8000/orders/1001/items
```

## API Client Scripts

The scripts in `api_clients/` call the FastAPI app with `curl`. They default to
`http://127.0.0.1:8000`.

```bash
./api_clients/list_customers.sh
./api_clients/get_customer.sh 1
./api_clients/customer_spend.sh
./api_clients/list_orders.sh open
./api_clients/get_order.sh 1001
./api_clients/create_order.sh
./api_clients/replace_order.sh 1003
./api_clients/update_order_status.sh 1001 shipped
./api_clients/delete_order.sh 1004
./api_clients/list_order_items.sh
./api_clients/list_order_items.sh 1001
./api_clients/get_order_item.sh 1
./api_clients/get_order_items.sh 1001
```

Use a different API base URL:

```bash
API_BASE_URL=http://127.0.0.1:9000 ./api_clients/get_order.sh 1001
```

## Direct SQL Scripts

The scripts in `scripts/` do not call the API. They connect directly to
`data/orders.db` with Python's built-in `sqlite3` module.

Customers:

```bash
python scripts/list_customers.py
python scripts/get_customer.py 1
python scripts/customer_spend.py
```

Orders:

```bash
python scripts/list_orders.py
python scripts/list_orders.py --status open
python scripts/get_order.py 1001
python scripts/create_order.py
python scripts/replace_order.py 1001
python scripts/update_order_status.py 1001 shipped
python scripts/delete_order.py 1004
```

Order items:

```bash
python scripts/list_order_items.py
python scripts/list_order_items.py --order-id 1001
python scripts/get_order_item.py 1
python scripts/get_order_items.py 1001
```

## Implementation Guide

Core modules:

- `src/api_talk/api.py`: FastAPI app, request models, routes, and HTMX handlers.
- `src/api_talk/queries.py`: database operations used by the API.
- `src/api_talk/db.py`: SQLite connection helpers and database paths.
- `src/api_talk/setup.py`: database setup logic used by `scripts/setup_data.py`.

Data files:

- `data/schema.sql`: table definitions and constraints.
- `data/seed.sql`: seed customers, orders, and order items.
- `data/orders.db`: generated SQLite database.

Supporting entry points:

- `scripts/`: direct SQLite command-line scripts.
- `api_clients/`: shell scripts that call the HTTP API.

## Adding a Read Operation

1. Add the SQL-backed function in `src/api_talk/queries.py`.
2. Add the FastAPI route in `src/api_talk/api.py`.
3. Add a direct script in `scripts/` if the operation should be available without
   HTTP.
4. Add a shell client in `api_clients/` if the operation should be easy to call
   from the command line.
5. Update this README with the new usage.

For collection and item reads, keep the standard shape:

- `GET /resources`
- `GET /resources/{resource_id}`
- Optional collection filters through query parameters, such as
  `GET /orders?status=open`.

## Adding a Write Operation

1. Add validation and database mutation logic in `src/api_talk/queries.py`.
2. Add or update Pydantic request models in `src/api_talk/api.py`.
3. Add the FastAPI route using the appropriate HTTP method.
4. Return `404` when the target resource does not exist.
5. Return `400` when the request is structurally valid JSON but violates a
   business rule.
6. Add matching direct and shell scripts when useful.

Current write endpoints:

- `POST /orders`
- `PUT /orders/{order_id}`
- `PATCH /orders/{order_id}/status`
- `DELETE /orders/{order_id}`

## Validation Rules

- Order status must be one of `open`, `shipped`, or `cancelled`.
- An order must have at least one item.
- Item quantity must be greater than zero.
- Item unit price must be zero or greater.
- Deleting an order also deletes its order items.

## Verification

Compile-check the Python files:

```bash
python -m compileall src scripts
```

Reset the database before manual testing:

```bash
python scripts/setup_data.py
```
