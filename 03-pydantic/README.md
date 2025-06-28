# 👨‍🍳 Section 3: Pydantic Data Validation - Recipe Master

Learn **Pydantic** by building a smart recipe validation system! Discover how Pydantic uses type hints to create powerful data models with automatic validation, error handling, and documentation.

## 🎯 What You'll Learn

- Pydantic BaseModel fundamentals
- Field validation with constraints and custom validators
- Nested models for complex data structures
- Error handling and user-friendly validation messages
- Advanced validation patterns for real applications

## 👨‍🍳 Meet Recipe Master

Our cooking platform demonstrates Pydantic validation through recipe management:

**Key Features:**
- 🍳 Recipe creation with comprehensive validation
- 📊 Nutrition information modeling
- 🥘 Ingredient quantity and safety checks
- 🎯 Smart cooking time recommendations

## 🔥 Pydantic Fundamentals

### **Basic Model Definition**

```python
from pydantic import BaseModel, Field
from typing import List, Optional

class Recipe(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=10)
    prep_time_minutes: int = Field(..., gt=0, le=480)
    servings: int = Field(..., gt=0, le=50)
    difficulty: DifficultyLevel
    is_published: bool = True
```

### **Field Constraints**

```python
class ValidatedRecipe(BaseModel):
    name: str = Field(..., min_length=3, max_length=100)
    chef_email: EmailStr  # Automatic email validation
    calories_per_serving: int = Field(..., gt=50, le=2000)
    prep_time_minutes: int = Field(..., gt=5, le=240)
    
    # Custom validator for cooking logic
    @validator('prep_time_minutes')
    def prep_time_reasonable(cls, v):
        if v > 180:  # More than 3 hours
            raise ValueError('Prep time seems too long!')
        return v
```

## 🎯 Advanced Validation Patterns

### **1. Custom Validators**

```python
class SmartRecipe(BaseModel):
    ingredients: List[Ingredient] = Field(..., min_items=2)
    cook_time_minutes: int = Field(..., gt=0, le=600)
    difficulty: DifficultyLevel
    
    @validator('ingredients')
    def validate_ingredients(cls, v):
        if len(v) < 2:
            raise ValueError('Recipe needs at least 2 ingredients!')
        
        ingredient_names = [ing.name.lower() for ing in v]
        if 'flour' in ingredient_names and 'eggs' not in ingredient_names:
            raise ValueError('Recipes with flour usually need eggs!')
        return v
    
    @validator('cook_time_minutes')
    def cook_time_vs_difficulty(cls, v, values):
        difficulty = values.get('difficulty')
        if difficulty == DifficultyLevel.BEGINNER and v > 60:
            raise ValueError('Beginner recipes should cook under 1 hour!')
        return v
```

### **2. Nested Models**

```python
class Ingredient(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    quantity: float = Field(..., gt=0)
    unit: str = Field(..., min_length=1, max_length=20)
    notes: Optional[str] = Field(None, max_length=100)

class NutritionInfo(BaseModel):
    calories_per_serving: int = Field(..., gt=0, le=2000)
    protein_grams: float = Field(..., ge=0, le=200)
    carbs_grams: float = Field(..., ge=0, le=300)
    fat_grams: float = Field(..., ge=0, le=150)

class CompleteRecipe(BaseModel):
    name: str
    ingredients: List[Ingredient]
    nutrition: NutritionInfo
    instructions: List[str] = Field(..., min_items=1)
```

### **3. Enum Validation**

```python
from enum import Enum

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
```

## 🚀 FastAPI Integration

Pydantic models automatically provide:

### **Request Validation**
```python
@app.post("/recipes/", response_model=RecipeResponse)
def create_recipe(recipe: RecipeCreate):
    # recipe is automatically validated
    # Invalid data returns 422 with detailed errors
    return create_new_recipe(recipe)
```

### **Response Models**
```python
class RecipeResponse(BaseModel):
    id: int
    name: str
    chef_email: EmailStr
    created_at: datetime
    difficulty: DifficultyLevel
    
    class Config:
        schema_extra = {
            "example": {
                "id": 1,
                "name": "Grandma's Chocolate Chip Cookies",
                "chef_email": "grandma@cookies.com",
                "difficulty": "intermediate"
            }
        }
```

## 🎮 Key Endpoints

### **Recipe Creation**
```python
@app.post("/recipes/validated/")
def create_validated_recipe(recipe: ValidatedRecipe):
    return {
        "message": "Recipe validated successfully!",
        "recipe_name": recipe.name,
        "total_time": recipe.prep_time_minutes + recipe.cook_time_minutes,
        "validation_status": "✅ All checks passed!"
    }
```

### **Complete Recipe with Ingredients**
```python
@app.post("/recipes/complete/")
def create_complete_recipe(recipe: RecipeWithIngredients):
    return {
        "recipe_name": recipe.name,
        "ingredient_count": len(recipe.ingredients),
        "calories_per_serving": recipe.nutrition.calories_per_serving,
        "chef_level": "🥇 Master Chef" if recipe.difficulty == DifficultyLevel.EXPERT else "👨‍🍳 Home Cook"
    }
```

## 🛠️ Running Recipe Master

```bash
cd 03-pydantic
pip install pydantic[email]  # For EmailStr validation
uvicorn main:app --reload

# Try these endpoints:
# POST /recipes/validated/
# POST /recipes/complete/
# POST /recipes/smart/
```

## 🔥 Validation Benefits

### **Automatic Error Messages**
```json
{
  "detail": [
    {
      "loc": ["body", "prep_time_minutes"],
      "msg": "ensure this value is greater than 5",
      "type": "value_error.number.not_gt"
    }
  ]
}
```

### **Type Conversion**
- Strings to integers/floats
- String booleans to actual booleans  
- ISO date strings to datetime objects
- JSON objects to nested models

### **Documentation Generation**
Pydantic models automatically generate JSON Schema for API documentation.

## 🎮 Practice Exercises

1. **🥗 Nutrition Calculator**: Create models that calculate nutritional values
2. **⏰ Meal Planner**: Build a weekly meal planning system with validation
3. **👨‍🍳 Chef Profiles**: Add chef validation with experience levels
4. **📊 Recipe Analytics**: Create models for recipe performance tracking

## 📊 Before vs After Pydantic

| Feature | Manual Validation | Pydantic Models |
|---------|------------------|-----------------|
| **Validation Code** | 50+ lines per model | 5-10 lines |
| **Error Messages** | Custom implementation | Automatic & clear |
| **Type Safety** | Runtime errors | Compile-time hints |
| **Documentation** | Manual writing | Auto-generated |
| **Testing** | Complex setup | Simple & reliable |

## 💡 Best Practices

1. **Field Constraints**: Use `Field()` for validation rules
2. **Custom Validators**: Add business logic validation  
3. **Response Models**: Always define response schemas
4. **Error Handling**: Provide helpful validation messages
5. **Examples**: Add schema examples for better docs

## 🚀 What's Next?

In **Section 4: Routing**, we'll build a digital library system that shows how to organize complex APIs with routers, dependencies, and advanced path operations!

**Key Takeaway**: Pydantic transforms data validation from tedious manual work into automatic, reliable, and well-documented processes! 👨‍🍳✨ 