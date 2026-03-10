from fastapi import FastAPI, Query
from pydantic import BaseModel, Field
from typing import Optional, List

app = FastAPI()

# ---------------- DATA ----------------

products = [
    {"id": 1, "name": "Wireless Mouse", "price": 499, "category": "Electronics", "in_stock": True},
    {"id": 2, "name": "Notebook", "price": 99, "category": "Stationery", "in_stock": True},
    {"id": 3, "name": "USB Hub", "price": 799, "category": "Electronics", "in_stock": False},
    {"id": 4, "name": "Pen Set", "price": 49, "category": "Stationery", "in_stock": True},
]

orders = []
feedback = []
order_counter = 1


# ---------------- MODELS ----------------

class OrderRequest(BaseModel):
    customer_name: str = Field(..., min_length=2)
    product_id: int = Field(..., gt=0)
    quantity: int = Field(..., gt=0)
    delivery_address: str = Field(..., min_length=10)


class CustomerFeedback(BaseModel):
    customer_name: str = Field(..., min_length=2, max_length=100)
    product_id: int = Field(..., gt=0)
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = Field(None, max_length=300)


class OrderItem(BaseModel):
    product_id: int = Field(..., gt=0)
    quantity: int = Field(..., ge=1, le=50)


class BulkOrder(BaseModel):
    company_name: str = Field(..., min_length=2)
    contact_email: str = Field(..., min_length=5)
    items: List[OrderItem]


# ---------------- HELPER ----------------

def find_product(product_id: int):
    for p in products:
        if p["id"] == product_id:
            return p
    return None


# ---------------- BASIC ENDPOINTS ----------------

@app.get("/")
def home():
    return {"message": "Welcome to our E-commerce API"}


@app.get("/products")
def get_products():
    return {"products": products}


# ---------------- Q1 ----------------

@app.get("/products/filter")
def filter_products(
    category: Optional[str] = Query(None),
    min_price: Optional[int] = Query(None),
    max_price: Optional[int] = Query(None),
    in_stock: Optional[bool] = Query(None)
):

    result = products

    if category:
        result = [p for p in result if p["category"] == category]

    if min_price:
        result = [p for p in result if p["price"] >= min_price]

    if max_price:
        result = [p for p in result if p["price"] <= max_price]

    if in_stock is not None:
        result = [p for p in result if p["in_stock"] == in_stock]

    return {"filtered_products": result, "count": len(result)}


# ---------------- Q4 ----------------

@app.get("/products/summary")
def product_summary():

    in_stock = [p for p in products if p["in_stock"]]
    out_stock = [p for p in products if not p["in_stock"]]

    most_expensive = max(products, key=lambda p: p["price"])
    cheapest = min(products, key=lambda p: p["price"])

    categories = list(set(p["category"] for p in products))

    return {
        "total_products": len(products),
        "in_stock_count": len(in_stock),
        "out_of_stock_count": len(out_stock),
        "most_expensive": {
            "name": most_expensive["name"],
            "price": most_expensive["price"]
        },
        "cheapest": {
            "name": cheapest["name"],
            "price": cheapest["price"]
        },
        "categories": categories
    }


# ---------------- Q2 ----------------

@app.get("/products/{product_id}/price")
def get_product_price(product_id: int):

    product = find_product(product_id)

    if not product:
        return {"error": "Product not found"}

    return {
        "name": product["name"],
        "price": product["price"]
    }


@app.get("/products/{product_id}")
def get_product(product_id: int):

    product = find_product(product_id)

    if not product:
        return {"error": "Product not found"}

    return {"product": product}


# ---------------- Q3 ----------------

@app.post("/feedback")
def submit_feedback(data: CustomerFeedback):

    feedback.append(data.dict())

    return {
        "message": "Feedback submitted successfully",
        "feedback": data.dict(),
        "total_feedback": len(feedback)
    }


# ---------------- ORDERS ----------------

@app.post("/orders")
def place_order(order: OrderRequest):

    global order_counter

    product = find_product(order.product_id)

    if not product:
        return {"error": "Product not found"}

    if not product["in_stock"]:
        return {"error": f"{product['name']} is out of stock"}

    order_data = {
        "order_id": order_counter,
        "customer_name": order.customer_name,
        "product": product["name"],
        "quantity": order.quantity,
        "delivery_address": order.delivery_address,
        "status": "pending"
    }

    orders.append(order_data)

    order_counter += 1

    return {
        "message": "Order placed successfully",
        "order": order_data
    }


@app.get("/orders")
def get_orders():
    return {"orders": orders}


# ---------------- BONUS ----------------

@app.get("/orders/{order_id}")
def get_order(order_id: int):

    for order in orders:
        if order["order_id"] == order_id:
            return {"order": order}

    return {"error": "Order not found"}


@app.patch("/orders/{order_id}/confirm")
def confirm_order(order_id: int):

    for order in orders:
        if order["order_id"] == order_id:
            order["status"] = "confirmed"

            return {
                "message": "Order confirmed",
                "order": order
            }

    return {"error": "Order not found"}


# ---------------- Q5 ----------------

@app.post("/orders/bulk")
def bulk_order(order: BulkOrder):

    confirmed = []
    failed = []
    grand_total = 0

    for item in order.items:

        product = find_product(item.product_id)

        if not product:

            failed.append({
                "product_id": item.product_id,
                "reason": "Product not found"
            })

        elif not product["in_stock"]:

            failed.append({
                "product_id": item.product_id,
                "reason": f"{product['name']} is out of stock"
            })

        else:

            subtotal = product["price"] * item.quantity
            grand_total += subtotal

            confirmed.append({
                "product": product["name"],
                "qty": item.quantity,
                "subtotal": subtotal
            })

    return {
        "company": order.company_name,
        "confirmed": confirmed,
        "failed": failed,
        "grand_total": grand_total
    }