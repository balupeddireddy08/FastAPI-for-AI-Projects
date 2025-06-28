from fastapi import FastAPI, HTTPException, Path, Query, Body, Form, File, UploadFile, status
from fastapi.responses import JSONResponse, HTMLResponse, Response
from pydantic import BaseModel, Field, EmailStr, validator, HttpUrl
from typing import List, Optional, Dict, Union
from datetime import datetime, date
import uuid

app = FastAPI(
    title="FastAPI Request-Response Demo",
    description="Demonstrating request and response models in FastAPI",
    version="0.1.0"
)

# Basic request/response models
class Item(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    tax: Optional[float] = None
    tags: List[str] = []

class ItemOut(BaseModel):
    name: str
    price: float
    tax: Optional[float] = None
    price_with_tax: Optional[float] = None

# User models for filtering sensitive data
class UserIn(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None

class UserOut(BaseModel):
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    
    class Config:
        schema_extra = {
            "example": {
                "username": "johndoe",
                "email": "john@example.com",
                "full_name": "John Doe"
            }
        }

# Models for the complete API example
class UserBase(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=100)

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)
    
    @validator('password')
    def password_must_be_strong(cls, v):
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one digit')
        if not any(char.isupper() for char in v):
            raise ValueError('Password must contain at least one uppercase letter')
        return v

class User(UserBase):
    id: int
    is_active: bool = True
    created_at: datetime

    class Config:
        orm_mode = True

class ItemBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    price: float = Field(..., gt=0)

class ItemCreate(ItemBase):
    seller_id: int = Field(..., gt=0)

class Item(ItemBase):
    id: int
    seller: User
    created_at: datetime

    class Config:
        orm_mode = True

# Custom exception
class ItemNotFoundError(Exception):
    def __init__(self, item_id: int):
        self.item_id = item_id
        self.message = f"Item with ID {item_id} not found"
        super().__init__(self.message)

# Exception handler
@app.exception_handler(ItemNotFoundError)
async def item_not_found_exception_handler(request, exc: ItemNotFoundError):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": exc.message},
    )

# Simple endpoints
@app.get("/")
def read_root():
    return {"message": "Request-Response Demo API"}

# Basic request body example
@app.post("/items/", response_model=Item)
def create_item(item: ItemCreate):
    """Create an item with a request body"""
    seller = {
        "id": item.seller_id,
        "email": "seller@example.com",
        "full_name": "Seller Name",
        "is_active": True,
        "created_at": datetime.now()
    }
    new_item = {
        "id": 1,
        "title": item.title,
        "description": item.description,
        "price": item.price,
        "seller": seller,
        "created_at": datetime.now()
    }
    return new_item

# Response model example
@app.post("/items/filter/", response_model=ItemOut)
def create_item_filtered(item: Item):
    """Create an item and return filtered response"""
    price_with_tax = item.price
    if item.tax:
        price_with_tax += item.price * item.tax
    return {
        "name": item.name,
        "price": item.price,
        "tax": item.tax,
        "price_with_tax": price_with_tax
    }

# User example with filtered response
@app.post("/users/", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(user: UserIn):
    """Create a user, filtering out password in response"""
    # In a real app, password would be hashed and stored
    return user

# Multiple body parameters
@app.post("/items/with-user/")
def create_item_with_user(item: Item, user: UserIn):
    """Create an item with user information"""
    return {"item": item, "user": user}

# Single value in body
@app.post("/items/importance/")
def create_item_with_importance(item: Item, importance: int = Body(..., gt=0)):
    """Create an item with an importance value"""
    return {"item": item, "importance": importance}

# Form data
@app.post("/login/")
def login(username: str = Form(...), password: str = Form(...)):
    """Login with form data"""
    # In a real app, validate credentials here
    return {"username": username}

# File upload
@app.post("/files/")
def create_file(file: bytes = File(...)):
    """Upload a file as bytes"""
    return {"file_size": len(file)}

@app.post("/uploadfile/")
def create_upload_file(file: UploadFile = File(...)):
    """Upload a file with metadata"""
    return {
        "filename": file.filename,
        "content_type": file.content_type
    }

# Status code example
@app.post("/items/create/", status_code=status.HTTP_201_CREATED)
def create_item_with_status(item: Item):
    """Create an item and return 201 Created status"""
    return item

# Different response types
@app.get("/html/", response_class=HTMLResponse)
def get_html():
    """Return an HTML response"""
    return """
    <html>
        <head>
            <title>FastAPI HTML Response</title>
        </head>
        <body>
            <h1>Hello World!</h1>
        </body>
    </html>
    """

@app.get("/custom-response/")
def get_custom_response():
    """Return a response with custom headers"""
    content = {"message": "Hello World"}
    headers = {"X-Custom-Header": "Custom Value"}
    return JSONResponse(content=content, headers=headers)

# Cookie example
@app.get("/cookie/")
def create_cookie():
    """Set a cookie in the response"""
    response = Response()
    response.set_cookie(key="session", value="abc123", httponly=True)
    return response

# Error handling
@app.get("/items/{item_id}/error")
def read_item_with_error(item_id: int):
    """Example of using HTTPException"""
    if item_id != 1:
        raise HTTPException(
            status_code=404,
            detail="Item not found",
            headers={"X-Error": "Item Not Found"}
        )
    return {"item_id": item_id, "name": "Example Item"}

# Custom error
@app.get("/items/{item_id}/custom-error")
def read_item_with_custom_error(item_id: int):
    """Example of using custom exception"""
    if item_id != 1:
        raise ItemNotFoundError(item_id)
    return {"item_id": item_id, "name": "Example Item"}

# Structured vs Unstructured calling
@app.post("/analyze/")
async def analyze_text(text: str = Body(...)):
    """Example of unstructured calling with raw text"""
    word_count = len(text.split())
    char_count = len(text)
    return {
        "word_count": word_count,
        "char_count": char_count,
        "sample": text[:50] + "..." if len(text) > 50 else text
    }

# Practice Exercise Solution

# Blog API Models
class AuthorBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    bio: Optional[str] = Field(None, max_length=1000)

class AuthorCreate(AuthorBase):
    password: str = Field(..., min_length=8)
    
    @validator("password")
    def password_strength(cls, v):
        if not any(char.isdigit() for char in v):
            raise ValueError("Password must contain at least one digit")
        if not any(char.isupper() for char in v):
            raise ValueError("Password must contain at least one uppercase letter")
        return v

class AuthorResponse(AuthorBase):
    id: str
    created_at: datetime
    
    class Config:
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "Jane Smith",
                "email": "jane@example.com",
                "bio": "Tech writer and Python enthusiast",
                "created_at": "2023-01-15T00:00:00"
            }
        }

class PostBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=10)
    
class PostCreate(PostBase):
    author_id: str

class PostResponse(PostBase):
    id: str
    publication_date: datetime
    author: AuthorResponse
    
    class Config:
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174001",
                "title": "Introduction to FastAPI",
                "content": "FastAPI is a modern web framework for building APIs...",
                "publication_date": "2023-01-15T12:00:00",
                "author": {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "name": "Jane Smith",
                    "email": "jane@example.com",
                    "bio": "Tech writer and Python enthusiast",
                    "created_at": "2023-01-15T00:00:00"
                }
            }
        }

# In-memory database for blog
AUTHORS_DB = {}
POSTS_DB = {}

# Blog API Endpoints
@app.post("/blog/authors/", response_model=AuthorResponse, status_code=status.HTTP_201_CREATED)
def create_author(author: AuthorCreate):
    """Create a new author (password excluded from response)"""
    author_id = str(uuid.uuid4())
    author_data = author.dict()
    # In a real app, password would be hashed
    password = author_data.pop("password")
    author_data["id"] = author_id
    author_data["created_at"] = datetime.now()
    
    AUTHORS_DB[author_id] = author_data
    return author_data

@app.post("/blog/posts/", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
def create_post(post: PostCreate):
    """Create a new blog post"""
    author_id = post.author_id
    if author_id not in AUTHORS_DB:
        raise HTTPException(status_code=404, detail="Author not found")
    
    post_id = str(uuid.uuid4())
    post_data = post.dict()
    post_data["id"] = post_id
    post_data["publication_date"] = datetime.now()
    post_data["author"] = AUTHORS_DB[author_id]
    
    POSTS_DB[post_id] = post_data
    return post_data

@app.get("/blog/posts/", response_model=List[PostResponse])
def list_posts(skip: int = 0, limit: int = 10):
    """List all blog posts with pagination"""
    posts = list(POSTS_DB.values())
    return posts[skip:skip+limit]

@app.get("/blog/posts/{post_id}", response_model=PostResponse)
def get_post(post_id: str):
    """Get a specific blog post by ID"""
    if post_id not in POSTS_DB:
        raise HTTPException(status_code=404, detail="Post not found")
    return POSTS_DB[post_id]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 