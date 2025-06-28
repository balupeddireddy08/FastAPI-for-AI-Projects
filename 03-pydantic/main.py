from fastapi import FastAPI, HTTPException, Path, Query
from pydantic import BaseModel, Field, validator, EmailStr
from typing import Dict, List, Optional
from datetime import datetime

app = FastAPI(
    title="Pydantic Demo API",
    description="Demonstrating Pydantic data validation with FastAPI",
    version="0.1.0"
)

# Basic Pydantic model
class User(BaseModel):
    id: int
    name: str
    email: str
    password: str
    is_active: bool = True
    created_at: datetime = datetime.now()
    tags: List[str] = []
    description: Optional[str] = None

# Pydantic model with validations
class ValidatedUser(BaseModel):
    id: int = Field(..., gt=0, description="User ID (must be positive)")
    name: str = Field(..., min_length=2, max_length=50, description="User's full name")
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., min_length=8, description="User's password (min 8 chars)")
    age: int = Field(..., ge=18, description="User's age (must be 18+)")
    is_active: bool = True
    
    # Custom validator for password complexity
    @validator('password')
    def password_must_be_complex(cls, v):
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one digit')
        if not any(char.isupper() for char in v):
            raise ValueError('Password must contain at least one uppercase letter')
        return v

# Nested Pydantic models
class Address(BaseModel):
    street: str
    city: str
    country: str
    postal_code: str

class UserWithAddress(BaseModel):
    name: str
    email: EmailStr
    addresses: List[Address]
    metadata: Dict[str, str] = {}

# Models for request and response
class UserIn(BaseModel):
    name: str
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    created_at: datetime
    
    class Config:
        schema_extra = {
            "example": {
                "id": 1,
                "name": "John Doe",
                "email": "john@example.com",
                "created_at": "2023-01-15T00:00:00"
            }
        }

# Practice Exercise Solution
class Dimensions(BaseModel):
    height: float = Field(..., gt=0)
    width: float = Field(..., gt=0)
    depth: float = Field(..., gt=0)

class Product(BaseModel):
    id: int = Field(..., gt=0)
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    price: float = Field(..., gt=0)
    is_in_stock: bool = True
    tags: List[str] = []
    dimensions: Dimensions
    
    @validator('tags')
    def tags_not_empty(cls, v):
        if len(v) == 0:
            raise ValueError('At least one tag must be provided')
        return v

# API routes
@app.get("/")
def read_root():
    return {"message": "Pydantic Demo API"}

@app.post("/users/", response_model=UserOut)
def create_user(user: UserIn):
    """Create a new user (password will be excluded from response)"""
    # In a real app, you would hash the password and store in DB
    new_user = {
        "id": 1,  # In a real app, this would be generated
        "name": user.name,
        "email": user.email,
        "created_at": datetime.now()
    }
    return new_user

@app.post("/users/validated/")
def create_validated_user(user: ValidatedUser):
    """Create a user with validation (all validation happens automatically)"""
    return {"id": user.id, "name": user.name, "email": user.email}

@app.post("/users/address/")
def create_user_with_address(user: UserWithAddress):
    """Create a user with nested address data"""
    return {
        "name": user.name,
        "email": user.email,
        "addresses_count": len(user.addresses),
        "cities": [addr.city for addr in user.addresses]
    }

@app.get("/items/{item_id}")
def read_item(
    item_id: int = Path(..., gt=0, description="The ID of the item"),
    q: Optional[str] = Query(None, min_length=3, max_length=50, description="Search query")
):
    """Demonstrate path and query parameter validation"""
    return {"item_id": item_id, "q": q}

# Practice exercise endpoint
@app.post("/products/")
def create_product(product: Product):
    """Create a product using the Product model with validation"""
    return {
        "id": product.id,
        "name": product.name,
        "price": product.price,
        "dimensions": {
            "volume": product.dimensions.height * product.dimensions.width * product.dimensions.depth
        },
        "tags": product.tags
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 