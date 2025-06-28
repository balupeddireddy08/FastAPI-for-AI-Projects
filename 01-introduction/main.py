from fastapi import FastAPI

# Create a FastAPI application instance for our Coffee Shop
app = FastAPI(
    title="☕ Brew Master Coffee Shop API",
    description="Welcome to Brew Master! The coolest coffee shop API for managing orders, menu, and customers",
    version="1.0.0"
)

# Welcome endpoint - like greeting customers at the door
@app.get("/")
def welcome_to_coffee_shop():
    """Welcome message for customers visiting our coffee shop API."""
    return {
        "message": "☕ Welcome to Brew Master Coffee Shop!",
        "description": "Your favorite neighborhood coffee shop, now with an API!",
        "todays_special": "Vanilla Latte with extra foam",
        "wifi_password": "BrewMaster2024"
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

# Search for coffee with filters - like asking barista for recommendations
@app.get("/menu/search/")
def search_coffee_menu(
    mood: str = None, 
    max_price: float = 10.0, 
    caffeine_level: str = None
):
    """Search our coffee menu based on your mood and preferences."""
    
    # Sample coffee data
    all_coffees = [
        {"name": "Espresso", "price": 2.50, "caffeine_level": "High", "mood": ["energetic", "focused"]},
        {"name": "Cappuccino", "price": 4.00, "caffeine_level": "Medium", "mood": ["cozy", "social"]},
        {"name": "Latte", "price": 4.50, "caffeine_level": "Medium", "mood": ["relaxed", "comfort"]},
        {"name": "Americano", "price": 3.00, "caffeine_level": "High", "mood": ["simple", "strong"]},
        {"name": "Decaf Herbal Tea", "price": 3.50, "caffeine_level": "None", "mood": ["calm", "evening"]}
    ]
    
    # Filter based on criteria
    results = []
    for coffee in all_coffees:
        if coffee["price"] <= max_price:
            if caffeine_level and coffee["caffeine_level"].lower() != caffeine_level.lower():
                continue
            if mood and mood.lower() not in [m.lower() for m in coffee["mood"]]:
                continue
            results.append(coffee)
    
    return {
        "search_criteria": {
            "mood": mood,
            "max_price": max_price,
            "caffeine_level": caffeine_level
        },
        "recommendations": results,
        "barista_note": f"Found {len(results)} perfect matches for you!"
    }

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