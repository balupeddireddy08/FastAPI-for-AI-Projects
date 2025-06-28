# 📚 Section 4: Routing - Magical Digital Library

Master **FastAPI routing** by building a comprehensive digital library system! Learn how to organize APIs with path parameters, query filters, route organization, and dependencies.

## 🎯 What You'll Learn

- HTTP methods and route definitions
- Path and query parameters
- Route organization with APIRouter
- Dependencies for shared logic
- Enum validation and route ordering

## 📚 Meet the Magical Digital Library

Our library system demonstrates advanced routing through book management:

**Key Features:**
- 📖 Book discovery and detailed views
- 👥 Book club creation and management
- 📊 Member profiles and reading tracking
- 🎯 Personalized recommendations
- 🔐 Library card authentication system

## 🚀 Core Routing Concepts

### **1. Basic Route Definitions**

```python
from fastapi import FastAPI

app = FastAPI(title="📚 Magical Digital Library")

@app.get("/")
def library_entrance():
    return {
        "message": "📚 Welcome to the Magical Digital Library!",
        "featured_book": "The Midnight Library",
        "reading_challenge": "Read 12 books this year! 🏆"
    }

@app.get("/books/")
def browse_books():
    return {"books": ["The Midnight Library", "Dune", "Atomic Habits"]}
```

### **2. Path Parameters**

```python
@app.get("/books/{book_id}")
def get_magical_book(book_id: int):
    magical_books = {
        1: {"title": "The Midnight Library", "author": "Matt Haig"},
        2: {"title": "Dune", "author": "Frank Herbert"},
        3: {"title": "Atomic Habits", "author": "James Clear"}
    }
    
    book = magical_books.get(book_id)
    if book:
        return {"book_id": book_id, **book}
    return {"error": "📚 Book not found in our magical collection!"}
```

### **3. Query Parameters**

```python
from typing import Optional

@app.get("/books/")
def discover_books(
    genre: Optional[str] = None,
    max_pages: int = 1000,
    quick_read: bool = False
):
    if quick_read:
        max_pages = min(max_pages, 300)
    
    return {
        "search_criteria": {
            "genre": genre or "all genres",
            "max_pages": max_pages,
            "quick_read_mode": quick_read
        }
    }
```

**Try these URLs:**
- `/books/?genre=fantasy`
- `/books/?genre=mystery&max_pages=400`
- `/books/?quick_read=true`

## 🎯 Advanced Routing Patterns

### **1. Enum Validation**

```python
from enum import Enum

class BookGenre(str, Enum):
    FANTASY = "fantasy"
    MYSTERY = "mystery"
    ROMANCE = "romance"
    SCI_FI = "sci_fi"

@app.get("/genre/{genre_name}")
def explore_genre(genre_name: BookGenre):
    descriptions = {
        BookGenre.FANTASY: "🐉 Enter realms of magic and epic quests!",
        BookGenre.MYSTERY: "🔍 Solve puzzles and uncover hidden truths!",
        BookGenre.ROMANCE: "💕 Experience heartwarming love stories!",
        BookGenre.SCI_FI: "🚀 Journey to futures beyond imagination!"
    }
    
    return {
        "genre": genre_name.value,
        "description": descriptions[genre_name],
        "books_available": 150
    }
```

### **2. Route Organization with APIRouter**

```python
from fastapi import APIRouter

# Create dedicated book clubs section
book_clubs_router = APIRouter(
    prefix="/book-clubs",
    tags=["👥 Book Clubs"],
    responses={404: {"description": "Book club not found"}}
)

@book_clubs_router.get("/")
def list_book_clubs():
    return {
        "clubs": [
            {"name": "Dragons & Coffee Book Club", "genre": "fantasy", "members": 45},
            {"name": "Mystery Solvers Society", "genre": "mystery", "members": 32}
        ]
    }

@book_clubs_router.post("/")
def create_book_club(name: str, genre: BookGenre):
    return {"message": f"Created {name} club for {genre} lovers! 🎉"}

# Include router in main app
app.include_router(book_clubs_router)
```

### **3. Dependencies for Shared Logic**

```python
from fastapi import Depends, Header, HTTPException

def get_library_card(x_library_card: Optional[str] = Header(None)):
    """Check library membership level"""
    if x_library_card == "GOLDEN_READER_2024":
        return {"level": "premium", "perks": ["unlimited_borrowing"]}
    elif x_library_card == "SILVER_READER_2024":
        return {"level": "standard", "perks": ["standard_borrowing"]}
    return {"level": "basic", "perks": ["limited_borrowing"]}

@app.get("/premium-books/")
def get_premium_books(library_card = Depends(get_library_card)):
    if library_card["level"] == "basic":
        raise HTTPException(status_code=403, detail="Premium library card required!")
    
    return {
        "premium_books": ["Exclusive Early Release", "Author's Personal Collection"],
        "your_level": library_card["level"]
    }
```

## ⚠️ Important: Route Order

**Specific routes must come before general ones:**

```python
# ✅ CORRECT ORDER
@app.get("/members/me")  # Specific - comes first
def get_my_profile():
    return {"message": "Your personal reading profile!"}

@app.get("/members/{member_id}")  # General - comes second
def get_member_profile(member_id: str):
    return {"member": f"Profile for {member_id}"}

# ❌ WRONG ORDER - /members/me would never be reached!
```

## 🎮 Key API Endpoints

### **Book Management**
```python
@app.get("/books/{book_id}")               # Get specific book
@app.get("/books/")                        # Search books
@app.get("/genre/{genre_name}")            # Browse by genre
```

### **Book Clubs**  
```python
@app.get("/book-clubs/")                   # List all clubs
@app.post("/book-clubs/")                  # Create new club
@app.get("/book-clubs/{club_id}")          # Club details
```

### **Member Features**
```python
@app.get("/members/me")                    # My profile
@app.get("/daily-recommendation")          # Personalized picks
@app.get("/premium-books/")                # Premium content
```

## 🛠️ Running the Library

```bash
cd 04-routing
uvicorn main:app --reload

# Try these endpoints:
# GET /books/1
# GET /books/?genre=fantasy&max_pages=400
# GET /book-clubs/
# POST /book-clubs/ (create new club)
```

## 🎮 Practice Exercises

1. **📚 Reading Lists Router**: Create `/reading-lists/` with CRUD operations
2. **⭐ Reviews System**: Add `/books/{book_id}/reviews` endpoints  
3. **🎯 Advanced Search**: Add filters for author, publication year, rating
4. **🔐 Access Control**: Implement different permissions for member levels

## 📊 Routing Best Practices

| Practice | Description | Example |
|----------|-------------|---------|
| **Logical Grouping** | Group related endpoints | `/books/`, `/book-clubs/`, `/members/` |
| **Consistent Naming** | Use clear, predictable patterns | `/books/{id}` not `/book/{id}` |
| **HTTP Methods** | Use appropriate verbs | GET for read, POST for create |
| **Route Order** | Specific before general | `/me` before `/{id}` |
| **Dependencies** | Share common logic | Authentication, validation |

## 💡 Key Benefits

- **🏗️ Organization**: APIRouter keeps code modular
- **📖 Documentation**: Automatic grouping with tags
- **🔒 Security**: Dependencies handle authentication
- **🎯 Validation**: Enums ensure valid inputs
- **⚡ Performance**: Efficient route matching

## 🚀 What's Next?

In **Section 5: Request & Response**, we'll build a social media platform that shows how to handle complex data validation, file uploads, and structured API responses!

**Key Takeaway**: Good routing creates intuitive, maintainable APIs that scale beautifully with your application! 📚✨ 