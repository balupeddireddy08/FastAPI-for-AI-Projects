from typing import List, Optional, Dict, Any
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from enum import Enum
from pydantic import BaseModel

app = FastAPI(
    title="📚 Bookstore API - Type Hints Demo",
    description="A simple API to demonstrate how FastAPI uses type hints for validation and documentation.",
    version="1.0.0",
)

# Use an Enum to define a fixed set of choices for book genres
class BookGenre(str, Enum):
    FICTION = "fiction"
    NON_FICTION = "non_fiction"
    SCIENCE_FICTION = "science_fiction"
    FANTASY = "fantasy"
    MYSTERY = "mystery"

# Use Pydantic's BaseModel to define the structure of a book
# Type hints here are used for validation: FastAPI checks if incoming data matches these types.
class Book(BaseModel):
    title: str
    author: str
    genre: BookGenre
    price: float
    published_year: int
    is_bestseller: Optional[bool] = False # An optional boolean

# A simple in-memory "database" to store our books
bookstore_db: Dict[int, Book] = {}
next_book_id = 1

@app.post("/books/", summary="Add a new book to the store")
def add_book(book: Book) -> Dict[str, Any]:
    """
    Adds a new book to the bookstore.

    - The `book: Book` parameter tells FastAPI to expect a request body
      that matches the structure of the `Book` model.
    - FastAPI handles all the validation automatically based on the type hints
      in the `Book` class (`str`, `float`, `int`, `Enum`).
    - The return type hint `-> Dict[str, Any]` documents the response.
    """
    global next_book_id
    bookstore_db[next_book_id] = book
    response_data = {
        "message": f"Book '{book.title}' added successfully!",
        "book_id": next_book_id,
        "book_details": book.dict(),
    }
    next_book_id += 1
    return response_data

@app.get("/books/", summary="List all available books")
def list_books(genre: Optional[BookGenre] = None) -> List[Book]:
    """
    Lists all books in the bookstore.

    - The `genre: Optional[BookGenre]` query parameter allows filtering books
      by genre. It's optional and must be a valid `BookGenre`.
    - The return type hint `-> List[Book]` tells FastAPI (and developers)
      that this endpoint returns a list of `Book` objects.
    """
    if genre:
        # Return only books matching the specified genre
        return [
            book for book in bookstore_db.values() if book.genre == genre
        ]
    # Return all books if no genre is specified
    return list(bookstore_db.values())

@app.get("/", response_class=HTMLResponse, summary="Main Bookstore Interface")
async def read_root():
    """Serves the main HTML interface for the Bookstore API."""
    with open("index.html", encoding="utf-8") as f:
        return f.read()

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Bookstore API...")
    print("✅ Go to http://localhost:8000 to explore the API.")
    uvicorn.run(app, host="0.0.0.0", port=8000) 