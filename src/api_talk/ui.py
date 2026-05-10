import json
from html import escape
from typing import Literal
from urllib.parse import parse_qs

from fastapi import APIRouter, Query, Request
from fastapi.responses import HTMLResponse

from api_talk import queries

OrderStatus = Literal["open", "shipped", "cancelled"]

router = APIRouter()

SQL_LIST_CUSTOMERS = """
SELECT
    customers.id,
    customers.name,
    customers.segment,
    customers.region
FROM customers
ORDER BY customers.name
"""

SQL_GET_CUSTOMER = """
SELECT
    customers.id,
    customers.name,
    customers.segment,
    customers.region
FROM customers
WHERE customers.id = ?
"""

SQL_GET_ORDER = """
SELECT
    orders.id,
    customers.name AS customer_name,
    customers.segment AS customer_segment,
    customers.region AS customer_region,
    orders.order_date,
    orders.status,
    orders.total_amount
FROM orders
JOIN customers ON orders.customer_id = customers.id
WHERE orders.id = ?
"""

SQL_LIST_ORDERS = """
SELECT
    orders.id,
    customers.name AS customer_name,
    orders.order_date,
    orders.status,
    orders.total_amount
FROM orders
JOIN customers ON orders.customer_id = customers.id
ORDER BY orders.order_date, orders.id
"""

SQL_LIST_ORDERS_BY_STATUS = """
SELECT
    orders.id,
    customers.name AS customer_name,
    orders.order_date,
    orders.status,
    orders.total_amount
FROM orders
JOIN customers ON orders.customer_id = customers.id
WHERE orders.status = ?
ORDER BY orders.order_date, orders.id
"""

SQL_LIST_ORDER_ITEMS = """
SELECT
    order_items.id,
    order_items.order_id,
    customers.name AS customer_name,
    order_items.product_name,
    order_items.quantity,
    order_items.unit_price,
    order_items.quantity * order_items.unit_price AS line_total
FROM order_items
JOIN orders ON order_items.order_id = orders.id
JOIN customers ON orders.customer_id = customers.id
ORDER BY order_items.order_id, order_items.id
"""

SQL_LIST_ORDER_ITEMS_BY_ORDER = """
SELECT
    order_items.id,
    order_items.order_id,
    customers.name AS customer_name,
    order_items.product_name,
    order_items.quantity,
    order_items.unit_price,
    order_items.quantity * order_items.unit_price AS line_total
FROM order_items
JOIN orders ON order_items.order_id = orders.id
JOIN customers ON orders.customer_id = customers.id
WHERE order_items.order_id = ?
ORDER BY order_items.id
"""

SQL_GET_ORDER_ITEM = """
SELECT
    order_items.id,
    order_items.order_id,
    customers.name AS customer_name,
    order_items.product_name,
    order_items.quantity,
    order_items.unit_price,
    order_items.quantity * order_items.unit_price AS line_total
FROM order_items
JOIN orders ON order_items.order_id = orders.id
JOIN customers ON orders.customer_id = customers.id
WHERE order_items.id = ?
"""

SQL_GET_ORDER_ITEMS = """
SELECT
    order_items.product_name,
    order_items.quantity,
    order_items.unit_price,
    order_items.quantity * order_items.unit_price AS line_total
FROM order_items
WHERE order_items.order_id = ?
ORDER BY order_items.id
"""

SQL_CREATE_ORDER = """
INSERT INTO orders (customer_id, order_date, status, total_amount)
VALUES (?, ?, ?, ?);

INSERT INTO order_items (order_id, product_name, quantity, unit_price)
VALUES (?, ?, ?, ?);

-- Read back the created order:
""" + SQL_GET_ORDER.strip()

SQL_REPLACE_ORDER = """
UPDATE orders
SET customer_id = ?, order_date = ?, status = ?, total_amount = ?
WHERE id = ?;

DELETE FROM order_items WHERE order_id = ?;

INSERT INTO order_items (order_id, product_name, quantity, unit_price)
VALUES (?, ?, ?, ?);

-- Read back the replaced order:
""" + SQL_GET_ORDER.strip()

SQL_UPDATE_ORDER_STATUS = """
UPDATE orders SET status = ? WHERE id = ?;

-- Read back the updated order:
""" + SQL_GET_ORDER.strip()

SQL_DELETE_ORDER = """
DELETE FROM order_items WHERE order_id = ?;

DELETE FROM orders WHERE id = ?
"""

SQL_CUSTOMER_SPEND = """
SELECT
    customers.id AS customer_id,
    customers.name AS customer_name,
    customers.segment,
    customers.region,
    COUNT(orders.id) AS order_count,
    ROUND(SUM(orders.total_amount), 2) AS total_spend
FROM customers
JOIN orders ON customers.id = orders.customer_id
WHERE orders.status != 'cancelled'
GROUP BY customers.id, customers.name, customers.segment, customers.region
ORDER BY total_spend DESC
"""


@router.get("/ui", response_class=HTMLResponse)
def ui() -> str:
    return """
    <!doctype html>
    <html lang="en">
      <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Orders API Demo</title>
        <script src="https://unpkg.com/htmx.org@2.0.4"></script>
        <style>
          * {
            box-sizing: border-box;
          }
          html, body {
            max-width: 100%;
            overflow-x: hidden;
          }
          body {
            margin: 0;
            font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            background: #f6f7f9;
            color: #1f2933;
          }
          header {
            padding: 20px 28px;
            background: #ffffff;
            border-bottom: 1px solid #d8dee8;
          }
          main {
            display: grid;
            grid-template-columns: minmax(300px, 380px) minmax(0, 1fr);
            gap: 20px;
            min-width: 0;
            padding: 20px 28px;
          }
          section, .panel {
            min-width: 0;
            background: #ffffff;
            border: 1px solid #d8dee8;
            border-radius: 8px;
            padding: 16px;
          }
          h1, h2, h3 {
            margin: 0 0 10px;
            overflow-wrap: anywhere;
          }
          h1 {
            font-size: 24px;
          }
          h2 {
            font-size: 16px;
          }
          h3 {
            font-size: 14px;
          }
          .actions {
            display: grid;
            gap: 12px;
          }
          form {
            display: grid;
            gap: 8px;
            margin: 0;
            padding: 12px;
            border: 1px solid #e3e8ef;
            border-radius: 8px;
          }
          label {
            display: grid;
            gap: 4px;
            min-width: 0;
            font-size: 13px;
            font-weight: 600;
          }
          input, select, button {
            min-width: 0;
            font: inherit;
          }
          input, select {
            width: 100%;
            min-height: 34px;
            border: 1px solid #b7c0ce;
            border-radius: 6px;
            padding: 6px 8px;
            background: #ffffff;
          }
          button {
            min-height: 34px;
            border: 0;
            border-radius: 6px;
            padding: 8px 10px;
            color: #ffffff;
            background: #2457a6;
            cursor: pointer;
            overflow-wrap: anywhere;
          }
          button.secondary {
            background: #4b5563;
          }
          button.danger {
            background: #b42318;
          }
          table {
            width: 100%;
            table-layout: fixed;
            border-collapse: collapse;
            font-size: 14px;
          }
          th, td {
            padding: 8px;
            border-bottom: 1px solid #e3e8ef;
            text-align: left;
            vertical-align: top;
            overflow-wrap: anywhere;
            word-break: break-word;
          }
          dl {
            display: grid;
            grid-template-columns: minmax(90px, 160px) minmax(0, 1fr);
            gap: 8px 12px;
            margin: 0 0 12px;
          }
          dt {
            font-weight: 700;
          }
          dd {
            min-width: 0;
            margin: 0;
            overflow-wrap: anywhere;
          }
          pre {
            max-width: 100%;
            overflow-x: auto;
            white-space: pre-wrap;
            overflow-wrap: anywhere;
            padding: 12px;
            border-radius: 6px;
            background: #111827;
            color: #e5e7eb;
          }
          .stack {
            display: grid;
            align-content: start;
            gap: 12px;
            min-width: 0;
          }
          .muted {
            color: #5f6b7a;
            font-size: 14px;
          }
          .response-block {
            display: grid;
            gap: 14px;
          }
          .response-block h4 {
            margin: 0 0 6px;
            font-size: 13px;
            color: #3b4654;
          }
          .route {
            margin: 0;
            padding: 10px 12px;
            border-radius: 6px;
            background: #eef2f7;
            color: #111827;
            font-weight: 700;
            overflow-wrap: anywhere;
          }
          .request {
            background: #0f172a;
          }
          .response {
            background: #172033;
          }
          .subtable {
            display: grid;
            gap: 8px;
            margin-bottom: 14px;
          }
          .subtable:last-child {
            margin-bottom: 0;
          }
          @media (max-width: 860px) {
            header {
              padding: 18px 16px;
            }
            main {
              grid-template-columns: minmax(0, 1fr);
              padding: 16px;
            }
            dl {
              grid-template-columns: minmax(0, 1fr);
            }
          }
        </style>
      </head>
      <body>
        <header>
          <h1>Orders API Demo</h1>
          <div class="muted">Web Client</div>
        </header>
        <main>
          <section>
            <h2>API Actions</h2>
            <div class="actions">
              <form hx-get="/ui/customers" hx-target="#result" hx-swap="innerHTML">
                <h3>Customers</h3>
                <button type="submit">GET /customers</button>
              </form>

              <form hx-get="/ui/customer" hx-target="#result" hx-swap="innerHTML">
                <h3>Customer detail</h3>
                <label>
                  Customer ID
                  <input name="customer_id" value="1">
                </label>
                <button type="submit">GET /customers/{id}</button>
              </form>

              <form hx-get="/ui/customers/spend" hx-target="#result" hx-swap="innerHTML">
                <h3>Customer spend</h3>
                <button type="submit">GET /customers/spend</button>
              </form>

              <form hx-get="/ui/orders" hx-target="#result" hx-swap="innerHTML">
                <h3>Orders</h3>
                <label>
                  Status
                  <select name="status">
                    <option value="">all</option>
                    <option value="open" selected>open</option>
                    <option value="shipped">shipped</option>
                    <option value="cancelled">cancelled</option>
                  </select>
                </label>
                <button type="submit">GET /orders</button>
              </form>

              <form hx-get="/ui/order" hx-target="#result" hx-swap="innerHTML">
                <h3>Order detail</h3>
                <label>
                  Order ID
                  <input name="order_id" value="1001">
                </label>
                <button type="submit">GET /orders/{id}</button>
              </form>

              <form hx-post="/ui/orders" hx-target="#result" hx-swap="innerHTML">
                <h3>Create order</h3>
                <label>
                  Customer ID
                  <input name="customer_id" value="2">
                </label>
                <label>
                  Order date
                  <input name="order_date" value="2026-05-06">
                </label>
                <label>
                  Status
                  <select name="status">
                    <option value="open" selected>open</option>
                    <option value="shipped">shipped</option>
                    <option value="cancelled">cancelled</option>
                  </select>
                </label>
                <label>
                  Product
                  <input name="product_name" value="API Integration Workshop">
                </label>
                <label>
                  Quantity
                  <input name="quantity" value="1">
                </label>
                <label>
                  Unit price
                  <input name="unit_price" value="1200.00">
                </label>
                <button type="submit">POST /orders</button>
              </form>

              <form hx-put="/ui/order" hx-target="#result" hx-swap="innerHTML">
                <h3>Replace order</h3>
                <label>
                  Order ID
                  <input name="order_id" value="1001">
                </label>
                <label>
                  Customer ID
                  <input name="customer_id" value="1">
                </label>
                <label>
                  Order date
                  <input name="order_date" value="2026-05-07">
                </label>
                <label>
                  Status
                  <select name="status">
                    <option value="open" selected>open</option>
                    <option value="shipped">shipped</option>
                    <option value="cancelled">cancelled</option>
                  </select>
                </label>
                <label>
                  Product
                  <input name="product_name" value="API Demo Cleanup">
                </label>
                <label>
                  Quantity
                  <input name="quantity" value="1">
                </label>
                <label>
                  Unit price
                  <input name="unit_price" value="500.00">
                </label>
                <button type="submit" class="secondary">PUT /orders/{id}</button>
              </form>

              <form hx-patch="/ui/order/status" hx-target="#result" hx-swap="innerHTML">
                <h3>Update status</h3>
                <label>
                  Order ID
                  <input name="order_id" value="1001">
                </label>
                <label>
                  Status
                  <select name="status">
                    <option value="open">open</option>
                    <option value="shipped" selected>shipped</option>
                    <option value="cancelled">cancelled</option>
                  </select>
                </label>
                <button type="submit" class="secondary">PATCH /orders/{id}/status</button>
              </form>

              <form hx-delete="/ui/order" hx-target="#result" hx-swap="innerHTML">
                <h3>Delete order</h3>
                <label>
                  Order ID
                  <input name="order_id" value="1004">
                </label>
                <button type="submit" class="danger">DELETE /orders/{id}</button>
              </form>

              <form hx-get="/ui/order/items" hx-target="#result" hx-swap="innerHTML">
                <h3>Order items for order</h3>
                <label>
                  Order ID
                  <input name="order_id" value="1001">
                </label>
                <button type="submit">GET /orders/{id}/items</button>
              </form>

              <form hx-get="/ui/order-items" hx-target="#result" hx-swap="innerHTML">
                <h3>Order items</h3>
                <label>
                  Order ID filter
                  <input name="order_id" value="">
                </label>
                <button type="submit">GET /order-items</button>
              </form>

              <form hx-get="/ui/order-item" hx-target="#result" hx-swap="innerHTML">
                <h3>Order item detail</h3>
                <label>
                  Item ID
                  <input name="item_id" value="1">
                </label>
                <button type="submit">GET /order-items/{id}</button>
              </form>
            </div>
          </section>

          <section class="stack">
            <h2>End-to-end data</h2>
            <div id="result" class="panel">
              Select an API action.
            </div>
          </section>
        </main>
      </body>
    </html>
    """


@router.get("/ui/customers", response_class=HTMLResponse)
def ui_list_customers() -> str:
    return _response("GET /customers", SQL_LIST_CUSTOMERS, queries.list_customers())


@router.get("/ui/customer", response_class=HTMLResponse)
def ui_get_customer(customer_id: int) -> str:
    customer = queries.get_customer(customer_id)
    route = f"GET /customers/{customer_id}"
    if customer is None:
        return _message(
            route, SQL_GET_CUSTOMER, f"Customer {customer_id} was not found."
        )
    return _response(route, SQL_GET_CUSTOMER, customer)


@router.get("/ui/customers/spend", response_class=HTMLResponse)
def ui_customer_spend() -> str:
    return _response(
        "GET /customers/spend", SQL_CUSTOMER_SPEND, queries.customer_spend()
    )


@router.get("/ui/orders", response_class=HTMLResponse)
def ui_list_orders(status: str | None = Query(default=None)) -> str:
    status_filter = status or None
    if status_filter is not None and status_filter not in queries.VALID_STATUSES:
        return _message(
            f"GET /orders?status={status_filter}",
            SQL_LIST_ORDERS_BY_STATUS,
            f"Invalid status: {status_filter}",
        )
    sql = SQL_LIST_ORDERS_BY_STATUS if status_filter else SQL_LIST_ORDERS
    route = f"GET /orders?status={status_filter}" if status_filter else "GET /orders"
    return _response(route, sql, queries.list_orders(status=status_filter))


@router.post("/ui/orders", response_class=HTMLResponse)
async def ui_create_order(request: Request) -> str:
    form = await _urlencoded_form(request)
    request_body = _order_request_body(form)
    try:
        order = queries.create_order(
            customer_id=_form_int(form, "customer_id"),
            order_date=form.get("order_date", ""),
            status=form.get("status", ""),
            items=[_form_item(form)],
        )
    except ValueError as exc:
        return _message("POST /orders", SQL_CREATE_ORDER, str(exc), request_body)
    return _response("POST /orders", SQL_CREATE_ORDER, order, request_body)


@router.get("/ui/order", response_class=HTMLResponse)
def ui_get_order(order_id: int) -> str:
    order = queries.get_order(order_id)
    route = f"GET /orders/{order_id}"
    if order is None:
        return _message(route, SQL_GET_ORDER, f"Order {order_id} was not found.")
    return _response(route, SQL_GET_ORDER, order)


@router.put("/ui/order", response_class=HTMLResponse)
async def ui_replace_order(request: Request) -> str:
    form = await _urlencoded_form(request)
    order_id = _form_int(form, "order_id")
    request_body = _order_request_body(form)
    try:
        order = queries.replace_order(
            order_id=order_id,
            customer_id=_form_int(form, "customer_id"),
            order_date=form.get("order_date", ""),
            status=form.get("status", ""),
            items=[_form_item(form)],
        )
    except ValueError as exc:
        return _message(
            f"PUT /orders/{order_id}", SQL_REPLACE_ORDER, str(exc), request_body
        )

    if order is None:
        return _message(
            f"PUT /orders/{order_id}",
            SQL_REPLACE_ORDER,
            f"Order {order_id} was not found.",
            request_body,
        )
    return _response(f"PUT /orders/{order_id}", SQL_REPLACE_ORDER, order, request_body)


@router.patch("/ui/order/status", response_class=HTMLResponse)
async def ui_update_order_status(request: Request) -> str:
    form = await _urlencoded_form(request)
    order_id = _form_int(form, "order_id")
    status_value = form.get("status", "")
    route = f"PATCH /orders/{order_id}/status"
    request_body = {"status": status_value}
    if status_value not in queries.VALID_STATUSES:
        return _message(
            route,
            SQL_UPDATE_ORDER_STATUS,
            f"Invalid status: {status_value}",
            request_body,
        )

    order = queries.update_order_status(order_id, status_value)
    if order is None:
        return _message(
            route,
            SQL_UPDATE_ORDER_STATUS,
            f"Order {order_id} was not found.",
            request_body,
        )
    return _response(route, SQL_UPDATE_ORDER_STATUS, order, request_body)


@router.delete("/ui/order", response_class=HTMLResponse)
async def ui_delete_order(request: Request) -> str:
    form = await _urlencoded_form(request)
    order_id = _form_int(form, "order_id")
    route = f"DELETE /orders/{order_id}"
    deleted = queries.delete_order(order_id)
    if not deleted:
        return _message(route, SQL_DELETE_ORDER, f"Order {order_id} was not found.")
    return _message(route, SQL_DELETE_ORDER, f"Deleted order {order_id}.")


@router.get("/ui/order/items", response_class=HTMLResponse)
def ui_get_order_items(order_id: int) -> str:
    order = queries.get_order(order_id)
    route = f"GET /orders/{order_id}/items"
    if order is None:
        return _message(route, SQL_GET_ORDER, f"Order {order_id} was not found.")

    return _response(
        route,
        SQL_GET_ORDER + "\n\n" + SQL_GET_ORDER_ITEMS,
        {
            "order": order,
            "items": queries.get_order_items(order_id),
        },
    )


@router.get("/ui/order-items", response_class=HTMLResponse)
def ui_list_order_items(order_id: str | None = Query(default=None)) -> str:
    order_id_filter = int(order_id) if order_id else None
    if order_id_filter is not None and queries.get_order(order_id_filter) is None:
        return _message(
            f"GET /order-items?order_id={order_id_filter}",
            SQL_GET_ORDER,
            f"Order {order_id_filter} was not found.",
        )
    sql = (
        SQL_LIST_ORDER_ITEMS_BY_ORDER
        if order_id_filter is not None
        else SQL_LIST_ORDER_ITEMS
    )
    route = (
        f"GET /order-items?order_id={order_id_filter}"
        if order_id_filter is not None
        else "GET /order-items"
    )
    return _response(route, sql, queries.list_order_items(order_id=order_id_filter))


@router.get("/ui/order-item", response_class=HTMLResponse)
def ui_get_order_item(item_id: int) -> str:
    item = queries.get_order_item(item_id)
    route = f"GET /order-items/{item_id}"
    if item is None:
        return _message(
            route, SQL_GET_ORDER_ITEM, f"Order item {item_id} was not found."
        )
    return _response(route, SQL_GET_ORDER_ITEM, item)


async def _urlencoded_form(request: Request) -> dict[str, str]:
    body = (await request.body()).decode()
    parsed = parse_qs(body)
    return {key: values[-1] for key, values in parsed.items()}


def _form_int(form: dict[str, str], key: str) -> int:
    return int(form.get(key, "0") or "0")


def _form_item(form: dict[str, str]) -> dict:
    return {
        "product_name": form.get("product_name", ""),
        "quantity": _form_int(form, "quantity"),
        "unit_price": float(form.get("unit_price", "0") or "0"),
    }


def _order_request_body(form: dict[str, str]) -> dict:
    return {
        "customer_id": _form_int(form, "customer_id"),
        "order_date": form.get("order_date", ""),
        "status": form.get("status", ""),
        "items": [_form_item(form)],
    }


def _message(route: str, sql: str, message: str, request_body: dict | None = None) -> str:
    return _response(route, sql, {"message": message}, request_body)


def _response(route: str, sql: str, payload, request_body: dict | None = None) -> str:
    return f"""
    <div class="response-block">
      <div>
        <h4>Route</h4>
        <p class="route">{escape(route)}</p>
      </div>
      <div>
        <h4>Request</h4>
        <pre class="request">{escape(_json_block(request_body or {}))}</pre>
      </div>
      <div>
        <h4>Database query</h4>
        <pre class="query">{escape(sql.strip())}</pre>
      </div>
      <div>
        <h4>Response</h4>
        <pre class="response">{escape(_json_block(payload))}</pre>
      </div>
      <div>
        <h4>Data table</h4>
        {_table(payload)}
      </div>
    </div>
    """


def _json_block(payload) -> str:
    return json.dumps(payload, indent=2, default=str)


def _table(payload) -> str:
    if isinstance(payload, list):
        return _records_table(payload)
    if isinstance(payload, dict):
        return _dict_table(payload)
    return f"<p>{escape(str(payload))}</p>"


def _records_table(records: list[dict]) -> str:
    if not records:
        return "<p>No records found.</p>"

    headers = list(records[0].keys())
    heading_cells = "\n".join(f"<th>{escape(str(header))}</th>" for header in headers)
    body_rows = "\n".join(
        "<tr>"
        + "\n".join(
            f"<td>{escape(str(record.get(header, '')))}</td>" for header in headers
        )
        + "</tr>"
        for record in records
    )

    return f"""
    <table>
      <thead>
        <tr>{heading_cells}</tr>
      </thead>
      <tbody>{body_rows}</tbody>
    </table>
    """


def _dict_table(payload: dict) -> str:
    if all(not isinstance(value, (dict, list)) for value in payload.values()):
        return _records_table([payload])

    sections = []
    scalar_fields = {
        key: value
        for key, value in payload.items()
        if not isinstance(value, (dict, list))
    }
    if scalar_fields:
        sections.append(_subtable("Record", _records_table([scalar_fields])))

    for key, value in payload.items():
        if isinstance(value, list):
            table = (
                _records_table(value)
                if all(isinstance(item, dict) for item in value)
                else _records_table([{key: value}])
            )
            sections.append(_subtable(str(key), table))
        elif isinstance(value, dict):
            sections.append(_subtable(str(key), _dict_table(value)))

    return "\n".join(sections)


def _subtable(title: str, table_html: str) -> str:
    return f"""
    <div class="subtable">
      <h4>{escape(title)}</h4>
      {table_html}
    </div>
    """
