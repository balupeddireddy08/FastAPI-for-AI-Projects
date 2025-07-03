from typing import Dict, List, Optional, Union, Any
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from enum import Enum
import os
import random
from pydantic import BaseModel

app = FastAPI(
    title="🎮 Game Character Builder - Type Hints Demo",
    description="Explore Python type hints by building an RPG character creation API.",
    version="2.0.0"
)

# Serve HTML file directly
@app.get("/", response_class=HTMLResponse)
async def get_html():
    with open("type-hints/index.html", "r") as file:
        return file.read()

# Character classes enum for better type safety and auto-documentation
# FastAPI uses this Enum to provide dropdowns in the API docs, ensuring valid choices.
class CharacterClass(str, Enum):
    WARRIOR = "warrior"
    MAGE = "mage"
    ROGUE = "rogue"
    ARCHER = "archer"
    PALADIN = "paladin"

# Item type enum for inventory items
class ItemType(str, Enum):
    WEAPON = "weapon"
    ARMOR = "armor"
    POTION = "potion"
    ACCESSORY = "accessory"
    SCROLL = "scroll"

# Pydantic model for inventory items
class InventoryItem(BaseModel):
    name: str
    type: ItemType
    value: int
    weight: float
    description: Optional[str] = None

# Function with comprehensive type hints for character creation logic
# This function demonstrates: `str`, `Enum`, `int`, `float`, and `-> Dict[str, Any]` for return type.
# Type hints here improve readability and enable static analysis by tools like MyPy.
def create_character_profile(
    name: str, # `str` indicates a string (e.g., "HeroName")
    character_class: CharacterClass, # `CharacterClass` ensures valid enum value (e.g., CharacterClass.WARRIOR)
    level: int, # `int` indicates an integer (e.g., 1, 20, 100)
    health: float = 100.0, # `float` for decimal numbers (e.g., 85.5), with a default value
    mana: float = 50.0 # Another float parameter
) -> Dict[str, Any]: # `-> Dict[str, Any]` indicates the function returns a dictionary with string keys and any value type.
    """
    Creates a complete character profile for an RPG game.
    
    Type hints ensure correct data types are passed and returned.
    """
    # Define base stats for each character class.
    # `Dict[str, Dict[str, int]]` clearly types this nested dictionary.
    base_stats: Dict[CharacterClass, Dict[str, int]] = {
        CharacterClass.WARRIOR: {"strength": 18, "intelligence": 8, "agility": 12},
        CharacterClass.MAGE: {"strength": 6, "intelligence": 20, "agility": 10},
        CharacterClass.ROGUE: {"strength": 12, "intelligence": 14, "agility": 18},
        CharacterClass.ARCHER: {"strength": 14, "intelligence": 12, "agility": 16},
        CharacterClass.PALADIN: {"strength": 16, "intelligence": 12, "agility": 8}
    }
    
    # Retrieve stats based on the chosen character class, with a default if not found.
    stats: Dict[str, int] = base_stats.get(character_class, {"strength": 10, "intelligence": 10, "agility": 10})
    
    return {
        "name": name,
        "character_class": character_class.value, # Access enum value as a string
        "level": level,
        "health": health,
        "mana": mana,
        "stats": stats,
        "created_at": "2024-01-15T12:00:00Z",
        "is_active": True
    }

# Complex function showing advanced type usage for battle calculation
# Demonstrates: `Union`, `List`, `Optional`, and nested `Dict` with `float` values.
def calculate_battle_outcome(
    attacker_id: Union[int, str], # `Union[int, str]` means ID can be an integer or a string
    defender_id: Union[int, str], # Same for defender ID
    attack_type: str, # Type of attack (e.g., "sword_slash", "fireball")
    weapon_damage: int, # Base damage from weapon
    critical_hit: bool, # `bool` for true/false (e.g., True if it's a critical hit)
) -> Dict[str, Any]: # Returns a dictionary with mixed value types
    """
    Calculates the outcome of a battle.
    
    Advanced type hints ensure flexible yet validated inputs for complex game logic.
    """
    base_damage: float = float(weapon_damage) # Ensure float for calculations

    if critical_hit: # Apply critical hit bonus
        base_damage *= 2.0
    
    final_damage: float = base_damage
    
    # Generate attacker and defender names for display
    attacker_name = f"Hero-{attacker_id}" if isinstance(attacker_id, int) else attacker_id
    defender_name = f"Hero-{defender_id}" if isinstance(defender_id, int) else defender_id
    
    # Determine battle outcome
    outcome = "Victory!" if final_damage > 50 else "Minor damage dealt"
    winner = attacker_name if final_damage > 50 else defender_name
    
    return {
        "attacker_id": attacker_id,
        "defender_id": defender_id,
        "attacker_name": attacker_name,
        "defender_name": defender_name,
        "attack_type": attack_type,
        "damage": round(final_damage, 1), # Round for cleaner output
        "critical_hit": critical_hit,
        "outcome": outcome,
        "winner": winner
    }

# In-memory database of characters
characters_db: Dict[int, Dict[str, Any]] = {}
next_character_id: int = 1

# FastAPI endpoints with typed parameters
@app.get("/api", summary="Welcome to the Character Builder")
def game_lobby():
    """Provides a welcome message and basic info about the character builder.
    
    This simple endpoint demonstrates a basic GET request with a dictionary response.
    """
    return {
        "message": "🎮 Welcome to the Game Character Builder! Craft your legend.",
        "online_players": 1337,
        "featured_class": "🗡️ Legendary Warrior",
        "daily_bonus": "Double XP Weekend!"
    }

@app.get("/characters/{character_id}", summary="Get Character Details by ID")
def get_character_details(
    character_id: int, # Path parameter: FastAPI expects an integer here.
    include_inventory: bool = False # Query parameter: optional boolean, defaults to False.
) -> Dict[str, Any]: # Return type hint for the response structure.
    """
    Retrieves detailed information for a specific character.
    
    FastAPI's automatic type conversion simplifies parameter handling from URL paths and query strings.
    """
    # Try to get character from our database, or create a default one
    if character_id in characters_db:
        character_data = characters_db[character_id].copy()
    else:
        # Simulate character data retrieval from a database or storage.
        character_data: Dict[str, Any] = {
            "id": character_id,
            "name": f"Hero{character_id}",
            "class": "warrior",
            "level": 25,
            "health": 85.5,
            "mana": 42.3,
            "is_online": True,
            "last_login": "2024-01-15T10:30:00Z"
        }
    
    if include_inventory: # Conditionally add inventory based on `include_inventory` boolean
        # Generate some random inventory items
        character_data["inventory"] = [
            {
                "name": "Steel Sword",
                "type": "weapon",
                "value": 250,
                "weight": 5.5
            },
            {
                "name": "Leather Armor",
                "type": "armor",
                "value": 150,
                "weight": 8.0
            },
            {
                "name": "Health Potion",
                "type": "potion",
                "value": 50,
                "weight": 0.5,
                "description": "Restores 50 health points"
            }
        ]
        character_data["gold"] = 2500
    
    return character_data

@app.post("/characters/create/", summary="Create a New Character")
def create_new_character(
    name: str, # Required string input
    character_class: CharacterClass, # Required, validated against CharacterClass enum
    level: int = 1, # Optional integer with default value
    starting_health: float = 100.0, # Optional float with default value
    starting_mana: float = 50.0 # Optional float with default value
) -> Dict[str, Any]: # Returns a dictionary
    """
    Creates a brand new character for the adventure. 
    
    Type hints enable FastAPI's automatic data validation and provide rich, interactive documentation.
    """
    global next_character_id
    
    # Call the core logic function with type-hinted arguments.
    character = create_character_profile(name, character_class, level, starting_health, starting_mana)
    
    # Add to our database
    character_id = next_character_id
    character["id"] = character_id
    characters_db[character_id] = character
    next_character_id += 1
    
    # Add a message for the frontend
    character["message"] = f"Character {name} created successfully!"
    
    return character

@app.post("/battle/simulate/", summary="Simulate a Battle")
def simulate_battle(
    attacker_id: Union[int, str], # Can accept either an integer ID or a string name
    defender_id: Union[int, str], # Same for defender
    attack_type: str = "sword_slash", # Default string value
    weapon_damage: int = 25, # Default integer value
    critical_hit: bool = False, # Default boolean value
) -> Dict[str, Any]: # Returns a dictionary with battle outcome details
    """
    Simulates a battle between two characters, showcasing various complex type hints.
    
    This demonstrates how FastAPI handles diverse input types for powerful API design.
    """
    # Call the core battle logic function.
    return calculate_battle_outcome(
        attacker_id, defender_id, attack_type, weapon_damage, 
        critical_hit
    )


if __name__ == "__main__":
    import uvicorn
    print("🎮 Starting Game Character Builder (Type Hints Demo)...")
    print("🏰 Prepare for legendary adventures! Open your browser to http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000) 