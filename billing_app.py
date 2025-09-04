
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel



app = FastAPI(title="Billing API")

# Enable CORS for frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Products list
products = {
    "towel": 150,
    "baby oil": 250,
    "Baby Lotion": 120.0,
    "Baby Diapers": 450.0,
    "Feeding Bottle": 250.0,
    "Baby Soap": 60.0,
    "Baby Clothes Set": 800.0,
    "Toys": 300.0,
    "baby shampoo": 98,
    "gripe water 100ml": 30,
    "milk powder 1kg": 700,
    "rubber": 30,
    "socks": 60,
}

# Cart & total
cart = []
subtotal = 0.0
discount_percent = 0.0   # default discount


# Request models
class CartItem(BaseModel):
    product: str
    qty: int

class DiscountRequest(BaseModel):
    discount_percent: float  # discount %


# List products
@app.get("/products")
def get_products():
    return {"products": products}


# Add product to cart
@app.post("/cart/add")
def add_to_cart(item: CartItem):
    global subtotal
    if item.product not in products:
        raise HTTPException(status_code=404, detail="Product not found")
    price = products[item.product]
    amount = price * item.qty
    cart.append({
        "product": item.product,
        "price": price,
        "qty": item.qty,
        "amount": amount
    })
    subtotal += amount
    return calculate_bill()


# View cart with GST + Discount
@app.get("/cart")
def view_cart():
    return calculate_bill()


# Apply discount
@app.post("/cart/discount")
def apply_discount(req: DiscountRequest):
    global discount_percent
    discount_percent = req.discount_percent
    return calculate_bill()


# Remove product from cart (first match)
@app.delete("/cart/remove/{product}")
def remove_from_cart(product: str):
    global subtotal
    for item in cart:
        if item["product"] == product:
            subtotal -= item["amount"]
            cart.remove(item)
            return calculate_bill()
    raise HTTPException(status_code=404, detail="Product not in cart")


# Clear cart
@app.delete("/cart")
def clear_cart():
    global subtotal, discount_percent
    cart.clear()
    subtotal = 0
    discount_percent = 0
    return {"message": "Cart cleared", "cart": cart, "bill": calculate_bill()}


# Helper function to calculate bill
def calculate_bill():
    # Apply discount
    discount_amount = subtotal * (discount_percent / 100)
    discounted_subtotal = subtotal - discount_amount

    # GST 12% split as 6% CGST + 6% SGST
    cgst = discounted_subtotal * 0.06
    sgst = discounted_subtotal * 0.06
    grand_total = discounted_subtotal + cgst + sgst

    return {
        "cart": cart,
        "subtotal": subtotal,
        "discount_percent": discount_percent,
        "discount_amount": round(discount_amount, 2),
        "discounted_subtotal": round(discounted_subtotal, 2),
        "cgst": round(cgst, 2),
        "sgst": round(sgst, 2),
        "grand_total": round(grand_total, 2)
    }


# Serve HTML page
@app.get("/", response_class=HTMLResponse)
def home():
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()
    #uvicorn billing_app:app