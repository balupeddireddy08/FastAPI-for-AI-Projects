# --- Imports ---
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import List
from enum import Enum


# --- FastAPI Application Initialization ---
# Creates the FastAPI application instance.
# Provides metadata like title, description, and version for the auto-generated API documentation (Swagger UI).
app = FastAPI(
    title="👨‍🍳 Recipe Master API",
    description="Learn Pydantic with a simple recipe validation example.", # Simplified description
    version="1.0.0"
)

# Serve the HTML file for the root path
@app.get("/", response_class=HTMLResponse)
async def read_root():
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()

# --- Enum Definitions ---
# Enums define a fixed set of allowed values, ensuring data consistency and preventing invalid entries.
class DifficultyLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"  
    ADVANCED = "advanced"
    EXPERT = "expert"

class CuisineType(str, Enum):
    ITALIAN = "italian"
    MEXICAN = "mexican"
    ASIAN = "asian"
    FRENCH = "french"
    AMERICAN = "american"


# --- Pydantic Data Models ---
# These models define the structure and validation rules for our data.

# Simplified Ingredient model for SmartRecipe
class SmartIngredient(BaseModel):
    # Fields with basic validation using Pydantic's Field function:
    # - 'min_length': Ensures the string has a minimum number of characters.
    # - 'gt': Ensures the numeric value is greater than a specified number.
    name: str = Field(..., min_length=1, max_length=50)
    quantity: float = Field(..., gt=0)
    unit: str = Field(..., min_length=1, max_length=20)
    
    # Custom field validator for 'quantity'
    # This method uses the '@field_validator' decorator to apply custom validation logic
    # to a specific field ('quantity'). It checks if the quantity is within a reasonable range.
    @field_validator('quantity')
    def quantity_reasonable(cls, v):
        if v > 100:
            raise ValueError('Quantity seems very high! Double-check measurements.')
        return v

# Main Recipe model focusing on Pydantic validation
class SmartRecipe(BaseModel):
    # Basic fields with Pydantic Field validation:
    # - 'min_length' and 'max_length' for string lengths.
    # - 'description' for OpenAPI documentation, providing human-readable explanations.
    name: str = Field(..., min_length=3, max_length=100, description="Recipe name")
    description: str = Field(..., min_length=20, max_length=500, description="Detailed recipe description")
    difficulty: DifficultyLevel = Field(..., description="Recipe difficulty level")
    prep_time_minutes: int = Field(..., gt=0, le=300, description="Preparation time in minutes")
    cook_time_minutes: int = Field(..., gt=0, le=600, description="Cooking time in minutes")
    
    # Nested model validation:
    # Pydantic automatically validates each item in the 'ingredients' list
    # by applying the validation rules defined in the 'SmartIngredient' model.
    # 'min_items' ensures that the list contains at least one ingredient.
    ingredients: List[SmartIngredient] = Field(..., min_items=1, description="List of ingredients")
    cuisine_type: CuisineType
    
    # Custom field validator for 'ingredients'
    # This validator specifically checks if the 'ingredients' list is empty.
    # It demonstrates validating the content or properties of a list field.
    @field_validator('ingredients')
    def validate_ingredients(cls, v):
        if not v: # Ensure at least one ingredient
            raise ValueError('A recipe needs at least one ingredient!')
        return v
    
    # Custom model validator (runs after all field validators)
    # This method uses the '@model_validator(mode='after')' decorator.
    # It allows for cross-field validation, where the validity of the model depends
    # on the interaction or combination of multiple fields (e.g., total prep and cook time).
    @model_validator(mode='after')
    def total_time_check(self):
        total_time = self.prep_time_minutes + self.cook_time_minutes
        if total_time > 720: # Max 12 hours total (e.g., for simple recipes)
            raise ValueError('Total time exceeds 12 hours. Consider simplifying the recipe.')
        return self


# --- FastAPI Endpoint Definitions ---
# These functions define the API routes and handle incoming requests.

@app.get("/welcome")
def welcome_message():
    """Welcome to the Recipe Master API!"""
    # This endpoint simply returns a welcome message to the API.
    return {"message": "👨‍🍳 Welcome to Recipe Master API! Explore simple Pydantic validation."}

@app.post("/recipes/")
def create_recipe_simple(recipe: SmartRecipe): # Using SmartRecipe for basic creation
    """Create a new recipe with Pydantic validation."""
    # FastAPI automatically uses the 'SmartRecipe' Pydantic model to validate the incoming request body.
    # If the incoming data (JSON) does not conform to the 'SmartRecipe' model's rules (including Field constraints,
    # nested model validation, and custom validators), FastAPI will automatically return a
    # 422 Unprocessable Entity error with detailed validation messages. This shows Pydantic's power.
    return {
        "message": "Recipe received and validated!",
        "name": recipe.name,
        "difficulty": recipe.difficulty.value,
        "total_ingredients": len(recipe.ingredients)
    }

@app.post("/recipes/validate-advanced/")
def validate_advanced_recipe(recipe: SmartRecipe):
    """
    Validate a recipe with advanced Pydantic rules (custom validators).
    This endpoint directly uses the SmartRecipe model to show detailed validation.
    """
    # This endpoint specifically highlights the execution of the custom model validators
    # (like 'total_time_check') defined within the SmartRecipe model. If any custom
    # validation fails, FastAPI will again return a 422 error.
    total_time = recipe.prep_time_minutes + recipe.cook_time_minutes
    return {
        "message": "Advanced validation successful!",
        "recipe_name": recipe.name,
        "total_preparation_and_cooking_time": f"{total_time} minutes",
        "validation_status": "All Pydantic rules passed!"
    }


# --- Application Startup ---
# This block ensures that the application runs using Uvicorn when the script is executed directly.
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 