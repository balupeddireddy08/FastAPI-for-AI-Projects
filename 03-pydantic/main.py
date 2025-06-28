from fastapi import FastAPI, HTTPException, Path, Query
from pydantic import BaseModel, Field, validator, EmailStr
from typing import Dict, List, Optional
from datetime import datetime
from enum import Enum

app = FastAPI(
    title="👨‍🍳 Recipe Master API",
    description="Your smart cooking assistant! Discover, create, and share amazing recipes with automatic nutrition validation.",
    version="1.0.0"
)

# Enums for better validation
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
    INDIAN = "indian"
    MEDITERRANEAN = "mediterranean"

class DietaryRestriction(str, Enum):
    VEGETARIAN = "vegetarian"
    VEGAN = "vegan"
    GLUTEN_FREE = "gluten_free"
    KETO = "keto"
    PALEO = "paleo"
    DAIRY_FREE = "dairy_free"

# Basic Recipe model with validation
class Recipe(BaseModel):
    id: int
    name: str = Field(..., min_length=1, max_length=100, description="Recipe name")
    description: str = Field(..., min_length=10, description="What makes this recipe special?")
    chef_name: str = Field(..., min_length=2, max_length=50)
    prep_time_minutes: int = Field(..., gt=0, le=480, description="Prep time (max 8 hours)")
    cook_time_minutes: int = Field(..., gt=0, le=720, description="Cook time (max 12 hours)")
    servings: int = Field(..., gt=0, le=50, description="Number of servings")
    difficulty: DifficultyLevel
    cuisine_type: CuisineType
    is_published: bool = True
    created_at: datetime = datetime.now()
    tags: List[str] = []
    rating: Optional[float] = Field(None, ge=0, le=5, description="Average rating (0-5 stars)")

# Advanced Recipe model with comprehensive validation
class ValidatedRecipe(BaseModel):
    name: str = Field(..., min_length=3, max_length=100, description="Recipe name")
    description: str = Field(..., min_length=20, max_length=500, description="Detailed description")
    chef_email: EmailStr = Field(..., description="Chef's email address")
    prep_time_minutes: int = Field(..., gt=5, le=240, description="Prep time: 5 minutes to 4 hours")
    cook_time_minutes: int = Field(..., gt=1, le=480, description="Cook time: 1 minute to 8 hours") 
    servings: int = Field(..., gt=1, le=20, description="Servings: 1-20 people")
    difficulty: DifficultyLevel
    calories_per_serving: int = Field(..., gt=50, le=2000, description="Calories per serving")
    
    # Custom validator for reasonable cooking times
    @validator('prep_time_minutes')
    def prep_time_reasonable(cls, v, values):
        if v > 180:  # More than 3 hours prep
            raise ValueError('Prep time seems too long! Are you sure this isn\'t a multi-day recipe?')
        return v
    
    @validator('cook_time_minutes')
    def cook_time_makes_sense(cls, v, values):
        if 'prep_time_minutes' in values:
            total_time = v + values['prep_time_minutes']
            if total_time > 600:  # More than 10 hours total
                raise ValueError('Total cooking time over 10 hours! Consider breaking this into multiple recipes.')
        return v

# Nested models for complex recipe structure
class Ingredient(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    quantity: float = Field(..., gt=0)
    unit: str = Field(..., min_length=1, max_length=20, description="cups, tsp, lbs, etc.")
    notes: Optional[str] = Field(None, max_length=100, description="Optional preparation notes")

class NutritionInfo(BaseModel):
    calories_per_serving: int = Field(..., gt=0, le=2000)
    protein_grams: float = Field(..., ge=0, le=200)
    carbs_grams: float = Field(..., ge=0, le=300)
    fat_grams: float = Field(..., ge=0, le=150)
    fiber_grams: float = Field(..., ge=0, le=50)
    sugar_grams: float = Field(..., ge=0, le=100)

class RecipeWithIngredients(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    chef_email: EmailStr
    description: str = Field(..., min_length=10)
    ingredients: List[Ingredient] = Field(..., min_items=1, description="At least one ingredient required!")
    instructions: List[str] = Field(..., min_items=1, description="Step-by-step instructions")
    nutrition: NutritionInfo
    difficulty: DifficultyLevel
    cuisine_type: CuisineType
    dietary_restrictions: List[DietaryRestriction] = []
    prep_time_minutes: int = Field(..., gt=0, le=240)
    cook_time_minutes: int = Field(..., gt=0, le=480)
    servings: int = Field(..., gt=1, le=20)

# Request/Response models for API endpoints
class RecipeCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    chef_email: EmailStr
    description: str = Field(..., min_length=10)

class RecipeResponse(BaseModel):
    id: int
    name: str
    chef_email: EmailStr
    description: str
    created_at: datetime
    difficulty: DifficultyLevel
    cuisine_type: CuisineType
    average_rating: Optional[float] = None
    
    class Config:
        schema_extra = {
            "example": {
                "id": 1,
                "name": "Grandma's Secret Chocolate Chip Cookies",
                "chef_email": "grandma@cookies.com",
                "description": "The most amazing chocolate chip cookies with a secret ingredient!",
                "created_at": "2024-01-15T00:00:00",
                "difficulty": "intermediate",
                "cuisine_type": "american",
                "average_rating": 4.8
            }
        }

# Practice Exercise Solution - Smart Recipe Validator
class SmartIngredient(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    quantity: float = Field(..., gt=0)
    unit: str = Field(..., min_length=1, max_length=20)
    category: str = Field(..., description="produce, dairy, meat, etc.")
    is_organic: bool = Field(False, description="Is this ingredient organic?")
    
    @validator('quantity')
    def quantity_reasonable(cls, v, values):
        if v > 100:
            raise ValueError('Quantity seems very high! Double-check your measurements.')
        return v

class SmartRecipe(BaseModel):
    id: int = Field(..., gt=0)
    name: str = Field(..., min_length=3, max_length=100)
    description: str = Field(..., min_length=20, max_length=1000)
    difficulty: DifficultyLevel = Field(..., description="Recipe difficulty level")
    prep_time_minutes: int = Field(..., gt=0, le=300)
    cook_time_minutes: int = Field(..., gt=0, le=600)
    servings: int = Field(..., gt=1, le=25)
    ingredients: List[SmartIngredient] = Field(..., min_items=2, description="At least 2 ingredients needed")
    cuisine_type: CuisineType
    dietary_restrictions: List[DietaryRestriction] = []
    
    @validator('ingredients')
    def validate_ingredients(cls, v):
        if len(v) < 2:
            raise ValueError('A recipe needs at least 2 ingredients to be complete!')
        
        # Check for common ingredient combinations
        ingredient_names = [ing.name.lower() for ing in v]
        
        # Helpful suggestions based on ingredients
        if 'flour' in ingredient_names and 'eggs' not in ingredient_names and 'milk' not in ingredient_names:
            raise ValueError('Recipes with flour usually need eggs or milk. Consider adding them!')
            
        return v
    
    @validator('cook_time_minutes')
    def cook_time_vs_difficulty(cls, v, values):
        if 'difficulty' in values:
            difficulty = values['difficulty']
            if difficulty == DifficultyLevel.BEGINNER and v > 60:
                raise ValueError('Beginner recipes should cook in under 1 hour to keep things simple!')
            elif difficulty == DifficultyLevel.EXPERT and v < 30:
                raise ValueError('Expert recipes usually require more cooking time for complex techniques!')
        return v

# API endpoints
@app.get("/")
def recipe_kitchen_welcome():
    """Welcome to your smart cooking assistant!"""
    return {
        "message": "👨‍🍳 Welcome to Recipe Master!",
        "description": "Your AI-powered cooking companion",
        "featured_recipe": "Grandma's Secret Chocolate Chip Cookies",
        "daily_tip": "Always read the entire recipe before starting to cook!",
        "active_chefs": 15420
    }

@app.post("/recipes/", response_model=RecipeResponse)
def create_recipe(recipe: RecipeCreate):
    """Create a new recipe (basic version with automatic validation)"""
    # In a real app, you would save to database and generate ID
    new_recipe = {
        "id": 1,
        "name": recipe.name,
        "chef_email": recipe.chef_email,
        "description": recipe.description,
        "created_at": datetime.now(),
        "difficulty": DifficultyLevel.INTERMEDIATE,
        "cuisine_type": CuisineType.AMERICAN,
        "average_rating": None
    }
    return new_recipe

@app.post("/recipes/validated/")
def create_validated_recipe(recipe: ValidatedRecipe):
    """Create a recipe with comprehensive validation"""
    return {
        "message": "Recipe validated and created successfully!",
        "recipe_name": recipe.name,
        "chef_email": recipe.chef_email,
        "total_time_minutes": recipe.prep_time_minutes + recipe.cook_time_minutes,
        "difficulty": recipe.difficulty.value,
        "estimated_cost": "Calculated based on ingredients",
        "validation_status": "✅ All checks passed!"
    }

@app.post("/recipes/complete/")
def create_complete_recipe(recipe: RecipeWithIngredients):
    """Create a complete recipe with ingredients, nutrition, and full validation"""
    total_time = recipe.prep_time_minutes + recipe.cook_time_minutes
    
    # Calculate some fun stats
    ingredient_count = len(recipe.ingredients)
    instruction_count = len(recipe.instructions)
    
    return {
        "message": "🎉 Complete recipe created successfully!",
        "recipe_name": recipe.name,
        "chef": recipe.chef_email,
        "stats": {
            "total_ingredients": ingredient_count,
            "total_steps": instruction_count,
            "total_time_minutes": total_time,
            "time_per_serving": round(total_time / recipe.servings, 1),
            "calories_per_serving": recipe.nutrition.calories_per_serving
        },
        "cuisine": recipe.cuisine_type.value,
        "difficulty": recipe.difficulty.value,
        "dietary_info": recipe.dietary_restrictions,
        "chef_level": "🥇 Master Chef" if recipe.difficulty == DifficultyLevel.EXPERT else "👨‍🍳 Home Cook"
    }

@app.get("/recipes/{recipe_id}")
def get_recipe_details(
    recipe_id: int = Path(..., gt=0, description="The ID of the recipe"),
    include_nutrition: bool = Query(False, description="Include detailed nutrition info"),
    include_shopping_list: bool = Query(False, description="Generate shopping list")
):
    """Get detailed recipe information with optional extras"""
    
    # Mock recipe data
    recipe_data = {
        "id": recipe_id,
        "name": "Perfect Pasta Carbonara",
        "chef": "chef.mario@italy.com",
        "description": "Authentic Roman-style carbonara with eggs, cheese, and pancetta",
        "difficulty": "intermediate",
        "cuisine": "italian",
        "prep_time": 15,
        "cook_time": 20,
        "servings": 4,
        "rating": 4.7,
        "reviews": 342
    }
    
    if include_nutrition:
        recipe_data["nutrition"] = {
            "calories_per_serving": 425,
            "protein_grams": 18.5,
            "carbs_grams": 45.2,
            "fat_grams": 22.1,
            "chef_note": "Rich and satisfying comfort food!"
        }
    
    if include_shopping_list:
        recipe_data["shopping_list"] = [
            "1 lb spaghetti pasta",
            "4 large eggs",
            "1 cup Pecorino Romano cheese",
            "6 oz pancetta or guanciale",
            "Fresh black pepper",
            "Sea salt"
        ]
    
    return recipe_data

# Practice exercise endpoint
@app.post("/recipes/smart/")
def create_smart_recipe(recipe: SmartRecipe):
    """
    Create a recipe using the SmartRecipe model with advanced validation.
    
    This demonstrates:
    - Complex nested validation
    - Cross-field validation 
    - Helpful error messages
    - Smart suggestions based on ingredients
    """
    
    # Calculate recipe complexity score
    complexity_score = 0
    complexity_score += len(recipe.ingredients) * 2
    complexity_score += recipe.cook_time_minutes // 10
    complexity_score += {"beginner": 1, "intermediate": 3, "advanced": 5, "expert": 8}[recipe.difficulty.value]
    
    # Generate cooking tips based on difficulty
    cooking_tips = {
        DifficultyLevel.BEGINNER: "Take your time and read each step carefully!",
        DifficultyLevel.INTERMEDIATE: "Prep all ingredients before starting - mise en place is key!",
        DifficultyLevel.ADVANCED: "Pay attention to timing and temperature control.",
        DifficultyLevel.EXPERT: "Trust your instincts and adjust seasoning to taste."
    }
    
    return {
        "id": recipe.id,
        "name": recipe.name,
        "chef_rating": "⭐⭐⭐⭐⭐" if complexity_score > 30 else "⭐⭐⭐",
        "complexity_score": complexity_score,
        "total_time": recipe.prep_time_minutes + recipe.cook_time_minutes,
        "ingredient_count": len(recipe.ingredients),
        "cuisine": recipe.cuisine_type.value,
        "dietary_friendly": recipe.dietary_restrictions,
        "cooking_tip": cooking_tips[recipe.difficulty],
        "estimated_cost": f"${(len(recipe.ingredients) * 3.50):.2f}",
        "validation_status": "✅ Smart validation passed!",
        "chef_badge": f"🏅 {recipe.difficulty.value.title()} Chef"
    }

if __name__ == "__main__":
    import uvicorn
    print("👨‍🍳 Starting Recipe Master Kitchen...")
    print("🍳 Ready to create delicious recipes!")
    uvicorn.run(app, host="0.0.0.0", port=8000) 