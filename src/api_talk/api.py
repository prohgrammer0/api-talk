from typing import Literal

from fastapi import FastAPI, HTTPException, Query, status
from pydantic import BaseModel, Field

from api_talk import queries
from api_talk.ui import router as ui_router

OrderStatus = Literal["open", "shipped", "cancelled"]


class OrderItemIn(BaseModel):
    product_name: str
    quantity: int = Field(gt=0)
    unit_price: float = Field(ge=0)


class OrderIn(BaseModel):
    customer_id: int
    order_date: str
    status: OrderStatus = "open"
    items: list[OrderItemIn] = Field(min_length=1)


class OrderStatusIn(BaseModel):
    status: OrderStatus


app = FastAPI(
    title="Orders API Demo",
    description="Brown bag demo showing SQL queries exposed through a REST API.",
    version="0.1.0",
)
app.include_router(ui_router)


@app.get("/")
def root() -> dict:
    return {
        "message": "Orders API Demo",
        "docs": "/docs",
        "examples": [
            "/customers",
            "/customers/1",
            "/orders/1001",
            "/orders?status=open",
            "/order-items",
            "/order-items?order_id=1001",
            "/order-items/1",
            "POST /orders",
            "PUT /orders/1001",
            "PATCH /orders/1001/status",
            "DELETE /orders/1001",
            "/orders/1001/items",
            "/customers/spend",
            "/ui",
        ],
    }


@app.get("/customers")
def list_customers() -> list[dict]:
    return queries.list_customers()


@app.get("/customers/spend")
def customer_spend() -> list[dict]:
    return queries.customer_spend()


@app.get("/customers/{customer_id}")
def get_customer(customer_id: int) -> dict:
    customer = queries.get_customer(customer_id)
    if customer is None:
        raise HTTPException(
            status_code=404,
            detail=f"Customer {customer_id} was not found",
        )
    return customer


@app.get("/orders")
def list_orders(
    status: OrderStatus | None = Query(default=None),
) -> list[dict]:
    return queries.list_orders(status=status)


@app.post("/orders", status_code=status.HTTP_201_CREATED)
def create_order(order: OrderIn) -> dict:
    try:
        created_order = queries.create_order(
            customer_id=order.customer_id,
            order_date=order.order_date,
            status=order.status,
            items=[item.model_dump() for item in order.items],
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return created_order


@app.get("/orders/{order_id}")
def get_order(order_id: int) -> dict:
    order = queries.get_order(order_id)
    if order is None:
        raise HTTPException(status_code=404, detail=f"Order {order_id} was not found")
    return order


@app.put("/orders/{order_id}")
def replace_order(order_id: int, order: OrderIn) -> dict:
    try:
        replaced_order = queries.replace_order(
            order_id=order_id,
            customer_id=order.customer_id,
            order_date=order.order_date,
            status=order.status,
            items=[item.model_dump() for item in order.items],
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if replaced_order is None:
        raise HTTPException(status_code=404, detail=f"Order {order_id} was not found")
    return replaced_order


@app.patch("/orders/{order_id}/status")
def update_order_status(order_id: int, status_update: OrderStatusIn) -> dict:
    try:
        order = queries.update_order_status(order_id, status_update.status)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if order is None:
        raise HTTPException(status_code=404, detail=f"Order {order_id} was not found")
    return order


@app.delete("/orders/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_order(order_id: int) -> None:
    deleted = queries.delete_order(order_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Order {order_id} was not found")


@app.get("/orders/{order_id}/items")
def get_order_items(order_id: int) -> dict:
    order = queries.get_order(order_id)
    if order is None:
        raise HTTPException(status_code=404, detail=f"Order {order_id} was not found")

    return {
        "order": order,
        "items": queries.get_order_items(order_id),
    }


@app.get("/order-items")
def list_order_items(order_id: int | None = Query(default=None)) -> list[dict]:
    if order_id is not None and queries.get_order(order_id) is None:
        raise HTTPException(status_code=404, detail=f"Order {order_id} was not found")
    return queries.list_order_items(order_id=order_id)


@app.get("/order-items/{item_id}")
def get_order_item(item_id: int) -> dict:
    item = queries.get_order_item(item_id)
    if item is None:
        raise HTTPException(status_code=404, detail=f"Order item {item_id} was not found")
    return item
