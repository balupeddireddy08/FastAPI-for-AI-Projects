from fastapi import FastAPI

# Create a FastAPI application instance
app = FastAPI(
    title="FastAPI Introduction",
    description="A simple API to demonstrate FastAPI basics",
    version="0.1.0"
)

# Root endpoint
@app.get("/")
def read_root():
    """Return a welcome message."""
    return {
        "message": "Welcome to FastAPI!",
        "description": "This is a simple API to demonstrate FastAPI basics."
    }

# Path parameter example
@app.get("/items/{item_id}")
def read_item(item_id: int):
    """Return an item by ID."""
    return {"item_id": item_id}

# Query parameter example
@app.get("/search/")
def search_items(q: str = None, limit: int = 10):
    """Search for items with query parameters."""
    return {
        "query": q,
        "limit": limit,
        "results": [f"Result {i}" for i in range(1, min(limit + 1, 6))]
    }

# Practice exercise endpoint
@app.get("/square/{number}")
def calculate_square(number: int):
    """Return the square of a number."""
    return {"number": number, "square": number ** 2}

# If this file is run directly, start the application with Uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 