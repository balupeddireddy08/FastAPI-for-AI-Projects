from fastapi import FastAPI, APIRouter, HTTPException, Path, Query, Depends, Header
from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum

# Initialize the Magical Digital Library!
app = FastAPI(
    title="📚 Magical Digital Library",
    description="Explore FastAPI routing: path, query, and modular routes!",
    version="1.0.0"
)

# Enums for better organization
class BookGenre(str, Enum):
    FANTASY = "fantasy"
    MYSTERY = "mystery"
    SCI_FI = "sci_fi"
    ROMANCE = "romance"

# Simplified Book Model for routing examples
class BookInfo(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    author: str = Field(..., min_length=1, max_length=50)
    genre: BookGenre

# Simple dependency for demonstration
def get_library_card(x_library_card: Optional[str] = Header(None)):
    """Simulates a basic library card check"""
    if x_library_card == "VALID_CARD":
        return {"status": "active"}
    return {"status": "inactive"}

# === MAIN LIBRARY ROUTES ===

@app.get("/")
async def library_entrance():
    """Welcome to the Simplified Digital Library! ✨"""
    try:
        with open("index.html", "r", encoding="utf-8") as f:
            from fastapi.responses import HTMLResponse
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return {"message": "📚 Welcome to the Simplified Digital Library! Focus on Routing."}

# === BOOK DISCOVERY ROUTES (Focus on Parameters) ===

# Route with path parameter - Find specific book
@app.get("/books/{book_id}")
def get_book_by_id(
    book_id: int = Path(..., title="Book ID", description="The unique identifier of the book", ge=1)
):
    """
    Get book details by ID. Demonstrates Path Parameters. 📖
    """
    # Mock data for demonstration
    if book_id == 1:
        return {"id": 1, "title": "The FastAPI Guide", "author": "Coding Expert", "genre": "sci_fi"}
    elif book_id == 2:
        return {"id": 2, "title": "Python Routing Basics", "author": "Route Master", "genre": "mystery"}
    raise HTTPException(status_code=404, detail="Book not found")

# Route with query parameters - Search books
@app.get("/books/search/")
def search_books(
    keyword: str = Query(..., min_length=2, description="Keyword to search in title or author"),
    max_pages: Optional[int] = Query(None, description="Maximum pages a book should have", le=1000),
    genre: Optional[BookGenre] = Query(None, description="Filter by book genre")
):
    """
    Search for books using query parameters. Demonstrates Query Parameters. 🔍
    """
    results = []
    # Simplified mock search logic
    mock_books = [
        {"title": "FastAPI in Action", "author": "Dev Guru", "genre": BookGenre.SCI_FI, "pages": 400},
        {"title": "Mystery of the Missing Route", "author": "Enigma", "genre": BookGenre.MYSTERY, "pages": 250},
        {"title": "Romance with Routes", "author": "Love Codes", "genre": BookGenre.ROMANCE, "pages": 300}
    ]

    for book in mock_books:
        match_keyword = keyword.lower() in book["title"].lower() or keyword.lower() in book["author"].lower()
        match_pages = True if max_pages is None else book["pages"] <= max_pages
        match_genre = True if genre is None else book["genre"] == genre

        if match_keyword and match_pages and match_genre:
            results.append(book)
            
    return {"query": keyword, "max_pages": max_pages, "genre": genre, "found_books": results}

# Route with enum path parameter - Browse by genre
@app.get("/genres/{genre_name}")
def explore_genre(genre_name: BookGenre):
    """
    Explore books by genre. Demonstrates Enum Path Parameters. 🏰
    """
    return {"message": f"Exploring the {genre_name.value.title()} genre!", "genre": genre_name.value}


# === MODULAR ROUTING WITH APIRouter ===

# Create an APIRouter instance for a specific module, like 'users'.
# This helps organize endpoints into logical groups and can be prefixed.
user_router = APIRouter(
    prefix="/users",
    tags=["👤 Users"],
    responses={404: {"description": "User not found"}}
)

# Endpoint within the user_router
@user_router.get("/{user_id}")
def get_user_profile(user_id: int = Path(..., ge=1),
                     library_card = Depends(get_library_card)):
    """Get user profile by ID. Demonstrates APIRouter and Dependencies. 🆔"""
    if user_id == 101:
        return {"user_id": 101, "username": "ReaderOne", "card_status": library_card["status"]}
    raise HTTPException(status_code=404, detail="User not found")

# Include the router in the main FastAPI application
app.include_router(user_router)


# === ANOTHER MODULAR ROUTER: Book Management (Admin) ===

# Create a new APIRouter specifically for book management functionalities, 
# often used for administrative tasks.
book_management_router = APIRouter(
    prefix="/admin/books", # All endpoints in this router will start with /admin/books
    tags=["📚 Admin - Book Management"], # Tags for documentation
    responses={403: {"description": "Operation forbidden"}} # Common responses for admin operations
)

# Route to add a new book (POST request body)
@book_management_router.post("/")
def add_book(book: BookInfo, library_card = Depends(get_library_card)):
    """
    Add a new book to the library (Admin access).
    Demonstrates receiving a request body with an APIRouter.
    """
    if library_card["status"] != "active":
        raise HTTPException(status_code=403, detail="Access denied. Valid library card required.")
    
    # In a real application, you would save the book to a database.
    return {"message": "Book added successfully!", "book_title": book.title, "genre": book.genre.value}

# Route to update an existing book (PUT request body and path parameter)
@book_management_router.put("/{book_id}")
def update_book(book_id: int, book_update: BookInfo, library_card = Depends(get_library_card)):
    """
    Update an existing book's details (Admin access).
    Demonstrates path parameters and request bodies within an APIRouter.
    """
    if library_card["status"] != "active":
        raise HTTPException(status_code=403, detail="Access denied. Valid library card required.")

    # In a real application, you would update the book in a database.
    # Mock check if book exists
    if book_id not in [1, 2]: # Assuming book IDs 1 and 2 exist from previous mocks
        raise HTTPException(status_code=404, detail="Book to update not found.")

    return {"message": f"Book ID {book_id} updated successfully!", "new_title": book_update.title, "new_genre": book_update.genre.value}

# Include the new book_management_router in the main FastAPI application
app.include_router(book_management_router)


# --- Application Startup ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 