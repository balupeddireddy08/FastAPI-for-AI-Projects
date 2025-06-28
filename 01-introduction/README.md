# ☕ Section 1: FastAPI Introduction - Brew Master Coffee Shop

Welcome to **FastAPI**! We'll learn the fundamentals by building a coffee shop management API that handles orders, menu items, and customer recommendations.

## 🎯 What You'll Learn

- FastAPI application creation and structure
- Basic routing with path and query parameters
- Automatic API documentation generation
- HTTP methods and response handling
- Error handling and data validation basics

## ☕ Meet Brew Master Coffee Shop

Our coffee shop API demonstrates core FastAPI concepts through familiar business operations:

**Key Features:**
- 📋 Menu browsing and coffee details
- 🔍 Smart coffee recommendations by mood
- 💰 Price calculations with tips
- 📊 Basic business analytics

## 🚀 Core FastAPI Concepts

### 1. **FastAPI Application Setup**

```python
from fastapi import FastAPI

# Create your application instance
app = FastAPI(
    title="☕ Brew Master Coffee Shop API",
    description="Your neighborhood coffee shop, now with an API!",
    version="1.0.0"
)
```

### 2. **Basic Routing**

```python
# Simple GET endpoint
@app.get("/")
def welcome_to_coffee_shop():
    return {
        "message": "☕ Welcome to Brew Master Coffee Shop!",
        "todays_special": "Vanilla Latte with extra foam"
    }

# Path parameters
@app.get("/menu/coffee/{coffee_id}")
def get_coffee_by_id(coffee_id: int):
    coffee_menu = {
        1: {"name": "Espresso", "price": 2.50},
        2: {"name": "Latte", "price": 4.50}
    }
    return coffee_menu.get(coffee_id, {"error": "Coffee not found!"})
```

### 3. **Query Parameters**

```python
@app.get("/menu/search/")
def search_coffee_menu(
    mood: str = None, 
    max_price: float = 10.0, 
    caffeine_level: str = None
):
    # Filter coffee based on parameters
    return {"recommendations": filtered_coffees}
```

## 🛠️ Running Your Coffee Shop

```bash
# Install FastAPI and server
pip install fastapi uvicorn

# Start the development server
uvicorn main:app --reload

# Visit your API documentation
# 🎮 Interactive docs: http://localhost:8000/docs
# 📖 Alternative docs: http://localhost:8000/redoc
```

## 🎮 Try These Endpoints

1. **Welcome Page**: `GET /`
2. **Get Coffee**: `GET /menu/coffee/1`
3. **Search Menu**: `GET /menu/search/?mood=tired&caffeine_level=high`
4. **Calculate Total**: `GET /calculate/total/4.50?tip_percentage=20`

## 🔥 Key FastAPI Features

### **Automatic Documentation**
FastAPI generates interactive API docs automatically from your code. No extra work needed!

### **Type Safety**
Path parameters are automatically converted to the correct types:
```python
@app.get("/coffee/{coffee_id}")
def get_coffee(coffee_id: int):  # Automatically converts to integer
    return {"coffee_id": coffee_id}
```

### **Data Validation**
Invalid inputs return clear error messages automatically.

## 🏋️‍♀️ Practice Challenge

Extend your coffee shop with these features:

1. **☕ Full Menu Endpoint**: `GET /menu` - Return all available coffees
2. **⭐ Rating System**: `GET /rate/{coffee_id}/{rating}` - Rate coffees 1-5 stars  
3. **🔍 Advanced Search**: Add filters for size, temperature, dairy-free options
4. **💰 Daily Sales**: `GET /sales/today` - Mock daily revenue calculation

## 💡 What's Next?

In **Section 2: Type Hints**, we'll build a game character system that shows how Python's type system makes FastAPI even more powerful and error-proof!

**Key Takeaway**: FastAPI automatically handles routing, validation, and documentation - letting you focus on building great features! ☕✨ 