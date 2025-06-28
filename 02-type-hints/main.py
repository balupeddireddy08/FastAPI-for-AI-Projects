from typing import Dict, List, Optional, Union, Any
from fastapi import FastAPI
from enum import Enum

app = FastAPI(
    title="🎮 Epic Character Builder API",
    description="Create legendary heroes for your next adventure! Build characters with stats, skills, and equipment.",
    version="2.0.0"
)

# Type hints for game character attributes
player_name: str = "DragonSlayer99"
player_level: int = 42
health_points: float = 87.5
is_online: bool = True

# Character classes enum for better type safety
class CharacterClass(str, Enum):
    WARRIOR = "warrior"
    MAGE = "mage"
    ROGUE = "rogue"
    ARCHER = "archer"
    PALADIN = "paladin"

# Advanced type hints for character inventory
inventory: List[str] = ["Magic Sword", "Health Potion", "Dragon Scale"]
character_names: List[str] = ["Gandalf", "Legolas", "Aragorn", "Gimli"]

# Character stats with specific types
character_stats: Dict[str, Union[str, int, float, bool]] = {
    "name": "Thorin Oakenshield",
    "level": 45,
    "health": 95.5,
    "mana": 30.0,
    "is_alive": True,
    "class": "warrior"
}

# Optional equipment (might not have it)
legendary_weapon: Optional[str] = None
mount: Optional[str] = "Fire Dragon"

# Function with comprehensive type hints for character creation
def create_character_profile(
    name: str,
    character_class: CharacterClass,
    level: int,
    health: float = 100.0,
    mana: float = 50.0
) -> Dict[str, Any]:
    """
    Create a complete character profile for RPG games.
    
    Args:
        name: Character's chosen name
        character_class: The character's class (warrior, mage, etc.)
        level: Character's current level
        health: Starting health points
        mana: Starting mana points
        
    Returns:
        Complete character profile dictionary
    """
    # Calculate derived stats based on class
    base_stats = {
        CharacterClass.WARRIOR: {"strength": 18, "intelligence": 8, "agility": 12},
        CharacterClass.MAGE: {"strength": 6, "intelligence": 20, "agility": 10},
        CharacterClass.ROGUE: {"strength": 12, "intelligence": 14, "agility": 18},
        CharacterClass.ARCHER: {"strength": 14, "intelligence": 12, "agility": 16},
        CharacterClass.PALADIN: {"strength": 16, "intelligence": 12, "agility": 8}
    }
    
    stats = base_stats.get(character_class, {"strength": 10, "intelligence": 10, "agility": 10})
    
    return {
        "name": name,
        "class": character_class.value,
        "level": level,
        "health": health,
        "mana": mana,
        "stats": stats,
        "created_at": "2024-01-15T12:00:00Z",
        "is_active": True
    }

# Complex function showing advanced type usage
def calculate_battle_outcome(
    attacker_id: Union[int, str],
    defender_id: Union[int, str],
    attack_type: str,
    weapon_damage: int,
    critical_hit: bool,
    status_effects: List[str],
    battle_modifiers: Dict[str, float]
) -> Dict[str, Any]:
    """
    Calculate the outcome of a battle between two characters.
    
    Args:
        attacker_id: ID of the attacking character (can be int or string)
        defender_id: ID of the defending character
        attack_type: Type of attack being performed
        weapon_damage: Base weapon damage
        critical_hit: Whether this is a critical hit
        status_effects: List of active status effects
        battle_modifiers: Dictionary of battle modifiers
        
    Returns:
        Battle outcome with damage dealt and effects
    """
    base_damage = weapon_damage
    
    # Apply critical hit multiplier
    if critical_hit:
        base_damage *= 2.0
    
    # Apply status effects
    damage_multiplier = 1.0
    for effect in status_effects:
        if effect == "poison":
            damage_multiplier += 0.2
        elif effect == "blessed":
            damage_multiplier += 0.5
        elif effect == "weakened":
            damage_multiplier -= 0.3
    
    # Apply battle modifiers
    for modifier, value in battle_modifiers.items():
        damage_multiplier += value
    
    final_damage = base_damage * max(damage_multiplier, 0.1)  # Minimum 10% damage
    
    return {
        "attacker_id": attacker_id,
        "defender_id": defender_id,
        "attack_type": attack_type,
        "base_damage": weapon_damage,
        "critical_hit": critical_hit,
        "status_effects": status_effects,
        "final_damage": round(final_damage, 1),
        "battle_result": "victory" if final_damage > 50 else "minor_damage"
    }

# FastAPI endpoints with typed parameters
@app.get("/")
def game_lobby():
    """Welcome to the Epic Character Builder game lobby!"""
    return {
        "message": "🎮 Welcome to Epic Character Builder!",
        "online_players": 1337,
        "featured_class": "🗡️ Legendary Warrior",
        "daily_bonus": "Double XP Weekend!"
    }

@app.get("/characters/{character_id}")
def get_character_details(character_id: int, include_inventory: bool = False) -> Dict[str, Any]:
    """
    Get detailed information about a specific character.
    
    Args:
        character_id: The unique ID of the character
        include_inventory: Whether to include the character's inventory
        
    Returns:
        Character information dictionary
    """
    # Simulate character data
    character_data = {
        "id": character_id,
        "name": f"Hero{character_id}",
        "class": "warrior",
        "level": 25,
        "health": 85.5,
        "mana": 42.3,
        "is_online": True,
        "last_login": "2024-01-15T10:30:00Z"
    }
    
    if include_inventory:
        character_data["inventory"] = [
            "Steel Sword", 
            "Leather Armor", 
            "Health Potion x3",
            "Magic Ring of Protection"
        ]
        character_data["gold"] = 2500
    
    return character_data

# FastAPI endpoint using the complex character creation function
@app.post("/characters/create/")
def create_new_character(
    name: str,
    character_class: CharacterClass,
    level: int = 1,
    starting_health: float = 100.0,
    starting_mana: float = 50.0
) -> Dict[str, Any]:
    """
    Create a brand new character for your adventure!
    
    This endpoint demonstrates how type hints help FastAPI automatically:
    - Validate that level is an integer
    - Validate that health/mana are numbers
    - Provide dropdown for character classes in the docs
    - Convert string inputs to proper types
    """
    return create_character_profile(name, character_class, level, starting_health, starting_mana)

# Battle system endpoint
@app.post("/battle/simulate/")
def simulate_battle(
    attacker_id: Union[int, str],
    defender_id: Union[int, str],
    attack_type: str = "sword_slash",
    weapon_damage: int = 25,
    critical_hit: bool = False,
    status_effects: List[str] = [],
    battle_modifiers: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
    """
    Simulate a battle between two characters.
    
    This shows advanced type usage with Union types, Lists, and Optional parameters.
    """
    if battle_modifiers is None:
        battle_modifiers = {}
    
    return calculate_battle_outcome(
        attacker_id, defender_id, attack_type, weapon_damage, 
        critical_hit, status_effects, battle_modifiers
    )

# Leaderboard endpoint
@app.get("/leaderboard/")
def get_leaderboard(
    category: str = "level",
    limit: int = 10,
    character_class: Optional[CharacterClass] = None
) -> Dict[str, Any]:
    """Get the top players leaderboard with optional filtering."""
    
    # Simulate leaderboard data
    mock_players = [
        {"name": "DragonMaster", "level": 89, "class": "mage", "score": 15420},
        {"name": "ShadowBlade", "level": 87, "class": "rogue", "score": 14890},
        {"name": "HolyKnight", "level": 85, "class": "paladin", "score": 14200},
        {"name": "ElvenArcher", "level": 83, "class": "archer", "score": 13750},
        {"name": "IronWarrior", "level": 82, "class": "warrior", "score": 13500}
    ]
    
    # Filter by class if specified
    if character_class:
        mock_players = [p for p in mock_players if p["class"] == character_class.value]
    
    # Limit results
    mock_players = mock_players[:limit]
    
    return {
        "category": category,
        "character_class_filter": character_class.value if character_class else "all",
        "top_players": mock_players,
        "total_players": len(mock_players),
        "last_updated": "2024-01-15T12:00:00Z"
    }

# Practice exercise solution with comprehensive types
@app.get("/guild/recommend/")
def recommend_guild_members(
    player_id: Union[int, str],
    preferred_class: Optional[CharacterClass] = None,
    min_level: int = 1,
    max_level: int = 100,
    is_online_only: bool = True,
    skills: List[str] = [],
    search_criteria: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Recommend guild members based on comprehensive criteria.
    
    This demonstrates the most advanced type hint usage:
    - Union types for flexible IDs
    - Optional complex parameters
    - Lists of strings
    - Nested dictionaries with Any values
    """
    if search_criteria is None:
        search_criteria = {}
    
    # Mock recommendation logic
    recommendations = [
        {
            "id": "player_123",
            "name": "ElvenMage",
            "class": "mage",
            "level": 45,
            "is_online": True,
            "skills": ["fireball", "teleport", "healing"],
            "compatibility_score": 0.95
        },
        {
            "id": 456,
            "name": "DwarfWarrior", 
            "class": "warrior",
            "level": 38,
            "is_online": True,
            "skills": ["shield_bash", "charge", "intimidate"],
            "compatibility_score": 0.87
        }
    ]
    
    # Filter recommendations
    if preferred_class:
        recommendations = [r for r in recommendations if r["class"] == preferred_class.value]
    
    if is_online_only:
        recommendations = [r for r in recommendations if r["is_online"]]
    
    recommendations = [r for r in recommendations if min_level <= r["level"] <= max_level]
    
    return {
        "player_id": player_id,
        "search_criteria": {
            "preferred_class": preferred_class.value if preferred_class else None,
            "level_range": f"{min_level}-{max_level}",
            "online_only": is_online_only,
            "required_skills": skills,
            "additional_criteria": search_criteria
        },
        "recommendations": recommendations,
        "total_found": len(recommendations)
    }

if __name__ == "__main__":
    import uvicorn
    print("🎮 Starting Epic Character Builder...")
    print("🏰 Prepare for legendary adventures!")
    uvicorn.run(app, host="0.0.0.0", port=8000) 