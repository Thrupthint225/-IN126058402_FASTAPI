from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List

app = FastAPI()

# -----------------------------
# In-memory storage
# -----------------------------
products = [
    {"id": 1, "name": "Wireless Mouse", "price": 499, "category": "Electronics", "in_stock": True},
    {"id": 2, "name": "Notebook", "price": 99, "category": "Stationery", "in_stock": True},
    {"id": 3, "name": "USB Hub", "price": 799, "category": "Electronics", "in_stock": False},
    {"id": 4, "name": "Pen Set", "price": 49, "category": "Stationery", "in_stock": True}
]

feedback_list = []

# -----------------------------
# Pydantic Models
# -----------------------------
class CustomerFeedback(BaseModel):
    customer_name: str = Field(..., min_length=2)
    product_id: int = Field(..., gt=0)
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = Field(None, max_length=300)

class OrderItem(BaseModel):
    product_id: int = Field(..., gt=0)
    quantity: int = Field(..., ge=1, le=50)

class BulkOrder(BaseModel):
    company_name: str = Field(..., min_length=2)
    contact_email: str = Field(..., min_length=5)
    items: List[OrderItem] = Field(..., min_items=1)

class ProductCreate(BaseModel):
    name: str
    price: int
    category: str
    in_stock: bool

# -----------------------------
# Assignment 3 - Q1: Add Products
# -----------------------------
@app.post("/products")
def add_product(product: ProductCreate):
    for p in products:
        if p["name"].lower() == product.name.lower():
            raise HTTPException(status_code=400, detail="Product with this name already exists")
    new_id = max(p["id"] for p in products) + 1
    new_product = product.dict()
    new_product["id"] = new_id
    products.append(new_product)
    return {"message": "Product added", "product": new_product}

# -----------------------------
# Assignment 3 - Q2: Update Product
# -----------------------------
@app.put("/products/{product_id}")
def update_product(product_id: int, price: Optional[int] = None, in_stock: Optional[bool] = None):
    for p in products:
        if p["id"] == product_id:
            if price is not None:
                p["price"] = price
            if in_stock is not None:
                p["in_stock"] = in_stock
            return p
    raise HTTPException(status_code=404, detail="Product not found")

# -----------------------------
# Assignment 3 - Q3: Delete Product
# -----------------------------
@app.delete("/products/{product_id}")
def delete_product(product_id: int):
    for i, p in enumerate(products):
        if p["id"] == product_id:
            deleted = products.pop(i)
            return {"message": f"Product '{deleted['name']}' deleted"}
    raise HTTPException(status_code=404, detail="Product not found")

# -----------------------------
# Existing GET endpoints
# -----------------------------
@app.get("/products")
def get_products():
    return products

@app.get("/products/filter")
def filter_products(
    min_price: Optional[int] = Query(None),
    max_price: Optional[int] = Query(None),
    category: Optional[str] = Query(None)
):
    filtered = products
    if min_price is not None:
        filtered = [p for p in filtered if p["price"] >= min_price]
    if max_price is not None:
        filtered = [p for p in filtered if p["price"] <= max_price]
    if category is not None:
        filtered = [p for p in filtered if p["category"].lower() == category.lower()]
    return {"filtered_products": filtered, "count": len(filtered)}

@app.get("/products/{product_id}/price")
def get_product_price(product_id: int):
    for p in products:
        if p["id"] == product_id:
            return {"name": p["name"], "price": p["price"]}
    raise HTTPException(status_code=404, detail="Product not found")

# -----------------------------
# Assignment 2 Feedback Endpoint
# -----------------------------
@app.post("/feedback")
def submit_feedback(data: CustomerFeedback):
    feedback_list.append(data)
    return {"message": "Feedback submitted successfully", "feedback": data, "total_feedback": len(feedback_list)}

# -----------------------------
# Assignment 2 Product Summary
# -----------------------------
@app.get("/products/summary")
def product_summary():
    total_products = len(products)
    in_stock_count = len([p for p in products if p["in_stock"]])
    out_of_stock_count = total_products - in_stock_count
    most_expensive = max(products, key=lambda x: x["price"])
    cheapest = min(products, key=lambda x: x["price"])
    categories = list(set([p["category"] for p in products]))
    return {
        "total_products": total_products,
        "in_stock_count": in_stock_count,
        "out_of_stock_count": out_of_stock_count,
        "most_expensive": {"name": most_expensive["name"], "price": most_expensive["price"]},
        "cheapest": {"name": cheapest["name"], "price": cheapest["price"]},
        "categories": categories
    }

# -----------------------------
# Assignment 2 Bulk Order
# -----------------------------
@app.post("/orders/bulk")
def bulk_order(order: BulkOrder):
    confirmed = []
    failed = []
    grand_total = 0
    for item in order.items:
        product = next((p for p in products if p["id"] == item.product_id), None)
        if not product:
            failed.append({"product_id": item.product_id, "reason": "Product not found"})
        elif not product["in_stock"]:
            failed.append({"product_id": item.product_id, "reason": f"{product['name']} is out of stock"})
        else:
            subtotal = product["price"] * item.quantity
            grand_total += subtotal
            confirmed.append({"product": product["name"], "qty": item.quantity, "subtotal": subtotal})
    return {"company": order.company_name, "confirmed": confirmed, "failed": failed, "grand_total": grand_total}

# -----------------------------
# Assignment 4 - New Endpoints
# -----------------------------

# GET /products/audit - Inventory Summary (placed above GET /products/{product_id})
@app.get("/products/audit")
def products_audit():
    total_products = len(products)
    in_stock_products = [p for p in products if p.get("in_stock", False)]
    out_of_stock_products = [p for p in products if not p.get("in_stock", False)]
    
    in_stock_count = len(in_stock_products)
    out_of_stock_names = [p["name"] for p in out_of_stock_products]
    
    total_stock_value = sum(p["price"] * 10 for p in in_stock_products)  # each in-stock item × 10 units
    most_expensive = max(products, key=lambda p: p["price"], default=None)
    most_expensive_data = {"name": most_expensive["name"], "price": most_expensive["price"]} if most_expensive else None
    
    return {
        "total_products": total_products,
        "in_stock_count": in_stock_count,
        "out_of_stock_names": out_of_stock_names,
        "total_stock_value": total_stock_value,
        "most_expensive": most_expensive_data
    }

# PUT /products/discount - Category-Wide Discount (Bonus)
@app.put("/products/discount")
def apply_discount(category: str, discount_percent: int = Query(..., ge=1, le=99)):
    updated_products = []
    for p in products:
        if p["category"].lower() == category.lower():
            old_price = p["price"]
            new_price = int(old_price * (1 - discount_percent / 100))
            p["price"] = new_price
            updated_products.append({"name": p["name"], "old_price": old_price, "new_price": new_price})
    
    if not updated_products:
        return {"message": f"No products found in category '{category}'"}
    
    return {
        "message": f"Applied {discount_percent}% discount to {len(updated_products)} products in category '{category}'",
        "updated_products": updated_products
    }

# GET /products/{product_id} - Get Single Product
@app.get("/products/{product_id}")
def get_product(product_id: int):
    for p in products:
        if p["id"] == product_id:
            return p
    raise HTTPException(status_code=404, detail="Product not found")