from fastapi import FastAPI, Path, Query, Body, Depends, Security, HTTPException, status, Header
from fastapi.openapi.utils import get_openapi
from fastapi.security import APIKeyHeader, OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, EmailStr, validator, HttpUrl
from typing import List, Optional, Dict, Union
from enum import Enum
import uuid
from datetime import datetime, date

# =========================================================================
# SECTION 1: TOP-LEVEL DOCUMENTATION METADATA
#
# FastAPI uses the parameters passed to its constructor to generate the
# high-level information for your API documentation.
# =========================================================================

# Define metadata for organizing endpoints into logical groups (tags)
# This will create sections in the Swagger UI.
tags_metadata = [
    {
        "name": "General",
        "description": "General-purpose endpoints.",
    },
    {
        "name": "Items",
        "description": "Manage items in our system. We can add **Markdown** here!",
        "externalDocs": {
            "description": "Items Documentation",
            "url": "https://example.com/docs/items",
        },
    },
    {
        "name": "Security",
        "description": "Endpoints demonstrating security documentation.",
    },
]

app = FastAPI(
    # --- Basic Info ---
    title="🚀 FastAPI Documentation Demo",
    description="""
A comprehensive demonstration of **OpenAPI** and **Swagger UI** features using FastAPI.
    
### 🌟 Key Features Demonstrated:
*   Top-level API metadata (title, description, version).
*   Endpoint organization with tags.
*   Rich model documentation with Pydantic.
*   Detailed parameter and response documentation.
*   Security scheme definitions.
*   Advanced schema customization.
    """,
    version="1.0.0",
    
    # --- Contact & License ---
    contact={
        "name": "API Support",
        "url": "http://example.com/support",
        "email": "support@example.com",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    
    # --- Tags Metadata ---
    openapi_tags=tags_metadata,
    
    # --- Server Configuration ---
    # Useful for defining different environments (dev, staging, prod)
    servers=[
        {"url": "http://localhost:8000", "description": "Development Server"},
        {"url": "https://staging.example.com", "description": "Staging Server"},
        {"url": "https://api.example.com", "description": "Production Server"},
    ],
    
    # --- Custom Docs URLs ---
    # You can change the default URLs for the documentation interfaces.
    docs_url="/docs",  # URL for Swagger UI
    redoc_url="/redoc" # URL for ReDoc
)


# =========================================================================
# SECTION 2: DOCUMENTING MODELS WITH PYDANTIC
#
# Pydantic models are automatically converted into JSON Schema definitions
# in your OpenAPI document. Use `Field` to add rich metadata.
# =========================================================================

class ItemCategory(str, Enum):
    """Category of an item, presented as a dropdown in the docs."""
    ELECTRONICS = "electronics"
    CLOTHING = "clothing"
    FOOD = "food"
    TOOLS = "tools"

class Item(BaseModel):
    """A model representing an item, with rich metadata for documentation."""
    name: str = Field(
        ...,  # `...` indicates this field is required
        min_length=3,
        max_length=50,
        description="The name of the item.",
        example="Smartwatch"
    )
    description: Optional[str] = Field(
        None,  # This field is optional
        max_length=300,
        description="A detailed description of the item.",
        example="A wearable device that tracks fitness and notifications."
    )
    price: float = Field(
        ...,
        ge=0,  # Greater than or equal to 0
        description="The price of the item in USD.",
        example=299.99
    )
    category: ItemCategory = Field(
        ...,
        description="The category the item belongs to.",
        example=ItemCategory.ELECTRONICS
    )
    tags: List[str] = Field(
        [],
        description="A list of tags for discoverability.",
        example=["wearable", "tech", "gadget"]
    )
    
    # The `Config.schema_extra` provides a complete example of the model
    # which is shown in the "Example Value" section of the docs.
    class Config:
        schema_extra = {
            "example": {
                "name": "Electric Drill",
                "description": "A powerful cordless drill for home projects.",
                "price": 89.99,
                "category": "tools",
                "tags": ["power-tool", "diy", "home-improvement"]
            }
        }

# =========================================================================
# SECTION 3: DOCUMENTING ENDPOINTS, PARAMETERS, AND RESPONSES
#
# Decorator parameters and function docstrings are used to document
# each API endpoint.
# =========================================================================

@app.get(
    "/",
    tags=["General"],
    summary="Welcome Endpoint",
    description="A simple welcome message to verify the API is running."
)
def welcome():
    """
    This is the main welcome endpoint.
    
    It doesn't take any parameters and returns a simple JSON object.
    The content from this docstring will appear in the documentation under the
    main description.
    """
    try:
        with open("swagger_docx/index.html", "r", encoding="utf-8") as f:
            from fastapi.responses import HTMLResponse
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return {"message": "Welcome to the FastAPI Documentation Demo!"}


@app.get(
    "/items/",
    tags=["Items"],
    summary="Search for Items",
    response_model=List[Item],
    response_description="A list of items that match the search criteria."
)
def search_items(
    # `Query` is used to document query parameters.
    query: Optional[str] = Query(
        None,
        title="Search Query",
        description="A search string to filter items by name or description.",
        min_length=3,
        example="gadget"
    ),
    # The `Enum` automatically creates a dropdown in the docs.
    category: Optional[ItemCategory] = Query(
        None,
        description="Filter by item category."
    )
):
    """
    Search for items in the system.
    
    - You can filter by a **search query**.
    - You can also filter by **category**.
    """
    # In a real app, you would filter data here. We'll return a mock list.
    mock_item = Item.Config.schema_extra["example"]
    return [mock_item]


@app.post(
    "/items/",
    tags=["Items"],
    summary="Create a New Item",
    status_code=status.HTTP_201_CREATED,
    response_model=Item,
    response_description="The newly created item."
)
def create_item(
    # `Body` is used to document the request body.
    item: Item = Body(
        ...,
        description="The item data to create."
    )
):
    """
    Create a new item and store it in the system.
    
    The request body must be a valid `Item` object. The response will be
    the created item, including any server-generated fields (if any).
    """
    return item


@app.get(
    "/items/{item_id}",
    tags=["Items"],
    summary="Get a Specific Item",
    # The `responses` dictionary allows documenting multiple possible responses.
    responses={
        200: {
            "description": "Item found.",
            "content": {
                "application/json": {
                    "example": {"name": "Smartwatch", "price": 299.99}
                }
            }
        },
        404: {
            "description": "Item not found.",
            "content": {
                "application/json": {
                    "example": {"detail": "Item with ID 999 not found."}
                }
            }
        }
    }
)
def get_item(
    # `Path` is used to document path parameters.
    item_id: int = Path(
        ...,
        title="Item ID",
        description="The unique identifier of the item to retrieve.",
        ge=1, # Must be greater than or equal to 1
        example=123
    )
):
    """
    Retrieve a single item by its unique ID.
    
    If the item is found, it will be returned. If not, a `404 Not Found`
    error will be raised.
    """
    if item_id == 999: # Simulate a not-found case
        raise HTTPException(status_code=404, detail=f"Item with ID {item_id} not found.")
    
    # Return a mock item for demonstration
    return {"name": "Smartwatch", "price": 299.99, "category": "electronics"}


# =========================================================================
# SECTION 4: DOCUMENTING SECURITY
#
# FastAPI integrates with security schemes to document authentication
# and authorization requirements.
# =========================================================================

# Define the security scheme (in this case, an API key in the header)
api_key_header_scheme = APIKeyHeader(name="X-API-Key", description="Your secret API key.")

@app.get(
    "/secure-data/",
    tags=["Security"],
    summary="Access Protected Data",
    description="This endpoint requires an API key for access.",
    dependencies=[Depends(api_key_header_scheme)] # This enforces the security scheme
)
def get_secure_data(api_key: str = Depends(api_key_header_scheme)):
    """
    Access a secure endpoint.
    
    The Swagger UI will show an "Authorize" button where you can enter the
    `X-API-Key`. The key will then be automatically included in requests
    made from the documentation page.
    """
    # In a real app, you would validate the API key here.
    return {"message": "You have accessed the secure data!", "api_key_used": api_key}



# =========================================================================
# SECTION 5: RUNNING THE APP
# =========================================================================
if __name__ == "__main__":
    import uvicorn
    print("--- FastAPI Documentation Demo ---")
    print("Swagger UI: http://localhost:8000/docs")
    print("ReDoc: http://localhost:8000/redoc")
    uvicorn.run(app, host="0.0.0.0", port=8000) 