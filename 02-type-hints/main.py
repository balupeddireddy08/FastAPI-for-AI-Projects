from typing import Dict, List, Optional, Union, Any
from fastapi import FastAPI

app = FastAPI(
    title="FastAPI Type Hints Demo",
    description="A demonstration of type hints in FastAPI",
    version="0.1.0"
)

# Basic type hints for variables
name: str = "John Doe"
age: int = 30
height: float = 1.85
is_active: bool = True

# List with type annotation
numbers: List[int] = [1, 2, 3, 4, 5]
names: List[str] = ["Alice", "Bob", "Charlie"]

# Dictionary with type annotations
user_info: Dict[str, Union[str, int, bool]] = {
    "name": "John",
    "age": 30,
    "is_active": True
}

# Optional values
middle_name: Optional[str] = None
nickname: Optional[str] = "Johnny"

# Function with type hints
def calculate_bmi(weight: float, height: float) -> float:
    """
    Calculate BMI using weight in kg and height in meters.
    
    Args:
        weight: Weight in kilograms
        height: Height in meters
        
    Returns:
        Body Mass Index value
    """
    return weight / (height ** 2)

# Function with complex type hints
def process_user_data(
    user_id: Union[int, str],
    name: str,
    age: int,
    is_active: bool,
    tags: List[str],
    settings: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Process user data and return processed information.
    
    Args:
        user_id: User identifier (can be integer or string)
        name: User's full name
        age: User's age in years
        is_active: Whether the user is active
        tags: List of tags associated with the user
        settings: User settings as key-value pairs
        
    Returns:
        Processed user data
    """
    return {
        "id": user_id,
        "name": name,
        "age": age,
        "is_active": is_active,
        "tags": tags,
        "settings": settings,
        "processed": True
    }

# FastAPI route with typed parameters
@app.get("/users/{user_id}")
def get_user(user_id: int, include_details: bool = False) -> Dict[str, Any]:
    """
    Get user information by user ID.
    
    Args:
        user_id: The ID of the user to retrieve
        include_details: Whether to include detailed information
        
    Returns:
        User data dictionary
    """
    user_data = {
        "id": user_id,
        "name": "User " + str(user_id),
        "is_active": True
    }
    
    if include_details:
        user_data.update({
            "age": 30,
            "email": f"user{user_id}@example.com",
            "registration_date": "2023-01-15"
        })
    
    return user_data

# FastAPI route using the complex function
@app.post("/users/")
def create_user(
    name: str,
    age: int,
    is_active: bool = True,
    tags: List[str] = [],
    settings: Dict[str, Any] = {}
) -> Dict[str, Any]:
    """
    Create a new user with the provided information.
    """
    user_id = 123  # In a real app, this would be generated
    return process_user_data(user_id, name, age, is_active, tags, settings)

# Practice exercise solution
@app.get("/users/process/")
def user_processor(
    user_id: Union[int, str],
    name: str,
    age: int,
    is_active: bool = True,
    tags: List[str] = [],
    settings: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Process and return user data with proper type annotations."""
    if settings is None:
        settings = {}
    
    return process_user_data(user_id, name, age, is_active, tags, settings)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 