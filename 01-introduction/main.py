from fastapi import FastAPI
from fastapi.responses import HTMLResponse

# Create a FastAPI application instance for our Coffee Shop
app = FastAPI(
    title="☕ Brew Master Coffee Shop API",
    description="Welcome to Brew Master! The coolest coffee shop API for managing orders, menu, and customers",
    version="1.0.0"
)

# Serve the HTML file for the root path
@app.get("/", response_class=HTMLResponse)
async def read_root():
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()

# Welcome endpoint - like greeting customers at the door
@app.get("/welcome")
def welcome_to_coffee_shop():
    """Welcome message for customers visiting our coffee shop API."""
    return {
        "message": "☕ Welcome to Brew Master Coffee Shop!",
        "description": "Your favorite neighborhood coffee shop, now with an API!",
        "todays_special": "Vanilla Latte with extra foam",
        "wifi_password": "BrewMaster2024",
        "available_coffees": [
            {"id": 1, "name": "Espresso", "price": 2.50, "caffeine_level": "High"},
            {"id": 2, "name": "Cappuccino", "price": 4.00, "caffeine_level": "Medium"},
            {"id": 3, "name": "Latte", "price": 4.50, "caffeine_level": "Medium"},
            {"id": 4, "name": "Americano", "price": 3.00, "caffeine_level": "High"},
            {"id": 5, "name": "Frappuccino", "price": 5.50, "caffeine_level": "Low"}
        ]
    }

# Get specific coffee by ID - like ordering from the menu
@app.get("/menu/coffee/{coffee_id}")
def get_coffee_by_id(coffee_id: int):
    """Get details about a specific coffee from our menu."""
    # In a real app, this would fetch from a database
    coffee_menu = {
        1: {"name": "Espresso", "price": 2.50, "caffeine_level": "High"},
        2: {"name": "Cappuccino", "price": 4.00, "caffeine_level": "Medium"},
        3: {"name": "Latte", "price": 4.50, "caffeine_level": "Medium"},
        4: {"name": "Americano", "price": 3.00, "caffeine_level": "High"},
        5: {"name": "Frappuccino", "price": 5.50, "caffeine_level": "Low"}
    }
    
    coffee = coffee_menu.get(coffee_id)
    if coffee:
        return {"coffee_id": coffee_id, **coffee}
    return {"error": "Sorry, we don't have that coffee on our menu!"}

# Practice exercise - calculate coffee cost with tip
@app.get("/calculate/total/{coffee_price}")
def calculate_coffee_total(coffee_price: float, tip_percentage: int = 15):
    """Calculate total cost of your coffee including tip - because baristas deserve love!"""
    if coffee_price <= 0:
        return {"error": "Coffee can't be free! (Though we wish it could be)"}
    
    tip_amount = coffee_price * (tip_percentage / 100)
    total = coffee_price + tip_amount
    
    return {
        "coffee_price": coffee_price,
        "tip_percentage": f"{tip_percentage}%",
        "tip_amount": round(tip_amount, 2),
        "total_cost": round(total, 2),
        "barista_happiness": "😊" if tip_percentage >= 15 else "😐"
    }

# If this file is run directly, start the coffee shop!
if __name__ == "__main__":
    import uvicorn
    print("🔥 Starting up the coffee shop...")
    uvicorn.run(app, host="0.0.0.0", port=8000) 