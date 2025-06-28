from fastapi import FastAPI, APIRouter, HTTPException, Path, Query, Depends, Header
from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from enum import Enum

# Initialize main FastAPI application
app = FastAPI(
    title="FastAPI Routing Demo",
    description="A demonstration of routing concepts in FastAPI",
    version="0.1.0"
)

# Basic Models
class Item(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    tax: Optional[float] = None

class ModelType(str, Enum):
    alexnet = "alexnet"
    resnet = "resnet"
    lenet = "lenet"

# Simple dependency for demonstration
def get_query_token(token: Optional[str] = None):
    if token is None:
        return None
    return token

# Route with path parameter
@app.get("/items/{item_id}")
def read_item(
    item_id: int = Path(..., title="The ID of the item to get", ge=1),
    q: Optional[str] = Query(None, max_length=50)
):
    """
    Get an item by its ID with an optional query parameter.
    """
    return {"item_id": item_id, "q": q}

# Route with query parameters
@app.get("/items/")
def list_items(skip: int = 0, limit: int = 10, token: str = Depends(get_query_token)):
    """
    List items with pagination support and optional token.
    """
    items = [{"id": i, "name": f"Item {i}"} for i in range(skip, skip + limit)]
    if token:
        return {"items": items, "token": token}
    return {"items": items}

# Route with request body
@app.post("/items/", status_code=201)
def create_item(item: Item):
    """
    Create a new item from the provided data.
    """
    return {
        "item": item,
        "created": True
    }

# Route with request body and path parameter
@app.put("/items/{item_id}")
def update_item(item_id: int, item: Item):
    """
    Update an existing item.
    """
    return {"item_id": item_id, "item": item}

# Route with enum path parameter
@app.get("/models/{model_name}")
def get_model(model_name: ModelType):
    """
    Get information about a machine learning model.
    """
    if model_name == ModelType.alexnet:
        return {"model": model_name, "message": "Deep Learning FTW!"}
    if model_name.value == "lenet":
        return {"model": model_name, "message": "LeCNN all the images"}
    return {"model": model_name, "message": "Have some residuals"}

# Path parameter containing a path
@app.get("/files/{file_path:path}")
def read_file(file_path: str):
    """
    Read a file from the specified path.
    """
    return {"file_path": file_path}

# Path operation order example
@app.get("/users/me")
def read_current_user():
    """
    Get the current user's information.
    """
    return {"user_id": "me", "name": "Current User"}

@app.get("/users/{user_id}")
def read_user(user_id: str):
    """
    Get a specific user's information.
    """
    return {"user_id": user_id, "name": f"User {user_id}"}

# Hidden endpoint example
@app.get("/internal/", include_in_schema=False)
def internal_endpoint():
    """
    This endpoint is not included in the OpenAPI schema.
    """
    return {"internal": True}

# Practice Exercise Solution
class Book(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    author: str
    description: Optional[str] = None
    price: float = Field(..., gt=0)
    pages: int = Field(..., gt=0)
    genres: List[str] = []
    published: bool = True

# Create a sample book database
BOOKS_DB = {
    1: Book(
        title="The FastAPI Handbook",
        author="John Doe",
        description="A comprehensive guide to FastAPI",
        price=29.99,
        pages=250,
        genres=["Programming", "API Development", "Python"]
    ),
    2: Book(
        title="Advanced Python Patterns",
        author="Jane Smith",
        description="Design patterns for Python applications",
        price=34.99,
        pages=320,
        genres=["Programming", "Design Patterns", "Python"]
    )
}

# Create a router for book endpoints
books_router = APIRouter(
    prefix="/books",
    tags=["Books"],
    responses={404: {"description": "Book not found"}}
)

@books_router.get("/", response_model=List[Book])
def get_books(skip: int = 0, limit: int = 10):
    """
    Get a list of all books with pagination support.
    """
    books = list(BOOKS_DB.values())
    return books[skip:skip+limit]

@books_router.get("/{book_id}", response_model=Book)
def get_book(book_id: int = Path(..., title="The ID of the book to get", ge=1)):
    """
    Get a specific book by its ID.
    """
    if book_id not in BOOKS_DB:
        raise HTTPException(status_code=404, detail="Book not found")
    return BOOKS_DB[book_id]

@books_router.post("/", status_code=201, response_model=Book)
def create_book(book: Book):
    """
    Create a new book.
    """
    book_id = max(BOOKS_DB.keys()) + 1 if BOOKS_DB else 1
    BOOKS_DB[book_id] = book
    return book

@books_router.put("/{book_id}", response_model=Book)
def update_book(book_id: int, book: Book):
    """
    Update an existing book.
    """
    if book_id not in BOOKS_DB:
        raise HTTPException(status_code=404, detail="Book not found")
    BOOKS_DB[book_id] = book
    return book

@books_router.delete("/{book_id}", response_model=Dict[str, bool])
def delete_book(book_id: int):
    """
    Delete a book.
    """
    if book_id not in BOOKS_DB:
        raise HTTPException(status_code=404, detail="Book not found")
    del BOOKS_DB[book_id]
    return {"success": True}

# Root endpoint for books API
@app.get("/")
def read_root():
    """
    Welcome message for the Books API.
    """
    return {
        "message": "Welcome to the Books API",
        "documentation": "/docs",
        "endpoints": {
            "books": "/books"
        }
    }

# Include the books router in the main app
app.include_router(books_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 