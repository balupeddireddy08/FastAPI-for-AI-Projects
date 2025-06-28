from fastapi import FastAPI, APIRouter, HTTPException, Path, Query, Depends, Header
from pydantic import BaseModel, Field, EmailStr
from typing import Dict, List, Optional
from enum import Enum
from datetime import datetime, date
import uuid

# Initialize the Magical Digital Library!
app = FastAPI(
    title="📚 Magical Digital Library & Book Club",
    description="Welcome to the most enchanted library in the digital realm! Discover books, join reading clubs, and connect with fellow book lovers.",
    version="2.0.0"
)

# Enums for better organization
class BookGenre(str, Enum):
    FANTASY = "fantasy"
    MYSTERY = "mystery"
    ROMANCE = "romance"
    SCI_FI = "sci_fi"
    THRILLER = "thriller"
    BIOGRAPHY = "biography"
    SELF_HELP = "self_help"
    COOKING = "cooking"

class ReadingStatus(str, Enum):
    WANT_TO_READ = "want_to_read"
    CURRENTLY_READING = "currently_reading"
    FINISHED = "finished"
    DNF = "did_not_finish"  # Did Not Finish

class MembershipLevel(str, Enum):
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    PLATINUM = "platinum"

# Enhanced Book Models
class Book(BaseModel):
    id: int
    title: str = Field(..., min_length=1, max_length=200)
    author: str = Field(..., min_length=1, max_length=100)
    genre: BookGenre
    description: Optional[str] = Field(None, max_length=1000)
    pages: int = Field(..., gt=0, le=2000)
    isbn: Optional[str] = None
    publication_year: int = Field(..., ge=1000, le=2030)
    average_rating: Optional[float] = Field(None, ge=0, le=5)
    is_available: bool = True
    magical_properties: Optional[str] = Field(None, description="Special magical abilities this book might have")

class BookClub(BaseModel):
    id: int
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=10, max_length=500)
    current_book_id: Optional[int] = None
    member_count: int = Field(default=0, ge=0)
    meeting_day: str = Field(..., description="Day of the week for meetings")
    is_active: bool = True
    created_at: datetime = datetime.now()

class LibraryMember(BaseModel):
    id: int
    username: str = Field(..., min_length=3, max_length=30)
    email: EmailStr
    membership_level: MembershipLevel = MembershipLevel.BRONZE
    books_read_count: int = Field(default=0, ge=0)
    favorite_genres: List[BookGenre] = []
    joined_date: date = date.today()
    reading_streak_days: int = Field(default=0, ge=0)

# Simple dependency for demonstration - Library Card Validation
def get_library_card(x_library_card: Optional[str] = Header(None)):
    """Validate library card for premium features"""
    if x_library_card is None:
        return None
    if x_library_card == "GOLDEN_READER_2024":
        return {"level": "premium", "perks": ["unlimited_borrowing", "early_access"]}
    elif x_library_card == "SILVER_READER_2024":
        return {"level": "standard", "perks": ["standard_borrowing"]}
    return {"level": "basic", "perks": ["limited_borrowing"]}

# === MAIN LIBRARY ROUTES ===

@app.get("/")
def library_entrance():
    """Welcome to the Magical Digital Library! ✨"""
    return {
        "message": "📚 Welcome to the Magical Digital Library!",
        "description": "Where every book is an adventure waiting to happen",
        "todays_featured": "Harry Potter and the Philosopher's Stone",
        "total_books": 50000,
        "active_book_clubs": 25,
        "reading_challenge": "Read 12 books this year! 🏆",
        "library_hours": "24/7 - Because magic never sleeps! ✨"
    }

# === BOOK DISCOVERY ROUTES ===

# Route with path parameter - Find specific book
@app.get("/books/{book_id}")
def get_magical_book(
    book_id: int = Path(..., title="Book ID", description="The magical identifier of the book", ge=1),
    include_reviews: bool = Query(False, description="Include reader reviews and ratings"),
    library_card = Depends(get_library_card)
):
    """
    Discover a magical book by its unique identifier! 📖
    
    Each book in our library has its own special story and magical properties.
    """
    # Mock book database
    magical_books = {
        1: {
            "id": 1,
            "title": "The Midnight Library",
            "author": "Matt Haig",
            "genre": "fantasy",
            "pages": 288,
            "description": "A dazzling novel about infinite possibilities and redemption",
            "average_rating": 4.2,
            "magical_properties": "Shows alternate life paths",
            "availability": "✅ Available for immediate reading"
        },
        2: {
            "id": 2,
            "title": "Dune",
            "author": "Frank Herbert",
            "genre": "sci_fi",
            "pages": 688,
            "description": "The epic space opera that changed science fiction forever",
            "average_rating": 4.7,
            "magical_properties": "Grants visions of the future",
            "availability": "⏳ 2 people ahead in queue"
        },
        3: {
            "id": 3,
            "title": "The Seven Husbands of Evelyn Hugo",
            "author": "Taylor Jenkins Reid",
            "genre": "romance",
            "pages": 400,
            "description": "A captivating novel about love, ambition, and secrets",
            "average_rating": 4.6,
            "magical_properties": "Reveals hidden truths about love",
            "availability": "✅ Available for immediate reading"
        }
    }
    
    book = magical_books.get(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="📚 This book seems to have vanished into the magical mists! Try another ID.")
    
    response = book.copy()
    
    # Add premium features for library card holders
    if library_card and library_card["level"] in ["standard", "premium"]:
        response["premium_features"] = {
            "audiobook_available": True,
            "discussion_notes": "Available in the premium section",
            "author_interview": "Exclusive content unlocked! 🎤"
        }
    
    if include_reviews and library_card:
        response["reader_reviews"] = [
            {"reviewer": "BookLover123", "rating": 5, "comment": "Absolutely magical! Couldn't put it down! ✨"},
            {"reviewer": "ReadingWizard", "rating": 4, "comment": "Great character development and plot twists 📚"},
            {"reviewer": "NightReader", "rating": 5, "comment": "This book changed my perspective on life! 🌟"}
        ]
    
    return response

# Route with query parameters - Book discovery system
@app.get("/books/")
def discover_books(
    genre: Optional[BookGenre] = Query(None, description="Filter by your favorite genre"),
    max_pages: int = Query(1000, description="Maximum pages (for busy readers!)", le=2000),
    min_rating: float = Query(0.0, description="Minimum average rating", ge=0, le=5),
    quick_read: bool = Query(False, description="Books under 300 pages for quick adventures"),
    author: Optional[str] = Query(None, min_length=2, max_length=50, description="Search by author name"),
    library_card = Depends(get_library_card)
):
    """
    🔍 Discover your next literary adventure!
    
    Use our magical search system to find books that match your mood, time, and interests.
    """
    
    # Apply quick read filter
    if quick_read:
        max_pages = min(max_pages, 300)
    
    # Mock search results
    all_books = [
        {"title": "The Midnight Library", "author": "Matt Haig", "genre": "fantasy", "pages": 288, "rating": 4.2},
        {"title": "Atomic Habits", "author": "James Clear", "genre": "self_help", "pages": 320, "rating": 4.8},
        {"title": "The Thursday Murder Club", "author": "Richard Osman", "genre": "mystery", "pages": 368, "rating": 4.1},
        {"title": "Educated", "author": "Tara Westover", "genre": "biography", "pages": 334, "rating": 4.5},
        {"title": "The Silent Patient", "author": "Alex Michaelides", "genre": "thriller", "pages": 336, "rating": 4.3}
    ]
    
    # Apply filters
    filtered_books = []
    for book in all_books:
        if genre and book["genre"] != genre.value:
            continue
        if book["pages"] > max_pages:
            continue
        if book["rating"] < min_rating:
            continue
        if author and author.lower() not in book["author"].lower():
            continue
        filtered_books.append(book)
    
    # Add personalized recommendations based on library card
    recommendation_note = "📖 Browse our collection!"
    if library_card:
        if library_card["level"] == "premium":
            recommendation_note = "🌟 Premium member detected! Here are your personalized recommendations:"
        elif library_card["level"] == "standard":
            recommendation_note = "📚 Standard member perks active! Enjoy these curated selections:"
    
    return {
        "search_criteria": {
            "genre": genre.value if genre else "all",
            "max_pages": max_pages,
            "min_rating": min_rating,
            "quick_read_mode": quick_read,
            "author_search": author
        },
        "books_found": len(filtered_books),
        "recommendations": filtered_books,
        "librarian_note": recommendation_note,
        "reading_tip": "📝 Tip: Start with the highest rated book for a guaranteed great experience!"
    }

# Route with enum path parameter - Browse by genre
@app.get("/genre/{genre_name}")
def explore_genre(genre_name: BookGenre):
    """
    🏰 Explore the different realms of our magical library!
    
    Each genre is like a different wing of our enchanted library.
    """
    genre_descriptions = {
        BookGenre.FANTASY: {
            "description": "🐉 Enter realms of magic, dragons, and epic quests!",
            "mood": "Escape reality and embrace wonder",
            "popular_books": ["The Name of the Wind", "The Way of Kings", "The Midnight Library"],
            "reading_time": "Perfect for weekend adventures"
        },
        BookGenre.MYSTERY: {
            "description": "🔍 Solve puzzles and uncover hidden truths!",
            "mood": "Engage your detective mind",
            "popular_books": ["The Thursday Murder Club", "Gone Girl", "The Silent Patient"],
            "reading_time": "Great for evening mysteries"
        },
        BookGenre.ROMANCE: {
            "description": "💕 Experience love stories that warm the heart!",
            "mood": "Feel the butterflies and swoon",
            "popular_books": ["The Seven Husbands of Evelyn Hugo", "Beach Read", "The Hating Game"],
            "reading_time": "Perfect comfort reading"
        },
        BookGenre.SCI_FI: {
            "description": "🚀 Journey to futures beyond imagination!",
            "mood": "Explore infinite possibilities",
            "popular_books": ["Dune", "The Martian", "Project Hail Mary"],
            "reading_time": "Mind-expanding adventures"
        }
    }
    
    genre_info = genre_descriptions.get(genre_name, {
        "description": f"📚 Discover amazing {genre_name.value} books!",
        "mood": "Expand your horizons",
        "popular_books": ["Coming soon!"],
        "reading_time": "Always a good time to read"
    })
    
    return {
        "genre": genre_name.value.replace("_", " ").title(),
        "wing_of_library": f"The {genre_name.value.replace('_', ' ').title()} Wing",
        **genre_info,
        "books_available": 150,  # Mock count
        "new_arrivals_this_month": 12,
        "genre_challenge": f"Read 3 {genre_name.value.replace('_', ' ')} books this month! 🏆"
    }

# Path parameter containing paths - Browse library sections
@app.get("/library/{section_path:path}")
def browse_library_section(section_path: str):
    """
    🗃️ Navigate through different sections of our magical library!
    
    Our library is organized like a magical castle with many rooms and sections.
    """
    return {
        "section": section_path,
        "description": f"Welcome to the {section_path} section!",
        "atmosphere": "✨ Filled with magical knowledge and cozy reading nooks",
        "features": [
            "Comfortable reading chairs",
            "Magical lighting that adjusts to your needs",
            "Whispering books that recommend themselves",
            "Floating shelves that organize themselves"
        ],
        "current_visitors": 23,
        "recommendation": "Take your time and let the books call to you! 📚"
    }

# === BOOK CLUB ROUTES USING APIRouter ===

book_clubs_router = APIRouter(
    prefix="/book-clubs",
    tags=["📖 Book Clubs"],
    responses={404: {"description": "Book club not found in our magical realm"}}
)

@book_clubs_router.get("/")
def list_magical_book_clubs(
    active_only: bool = Query(True, description="Show only active clubs"),
    genre_focus: Optional[BookGenre] = Query(None, description="Filter by genre focus"),
    library_card = Depends(get_library_card)
):
    """
    🏛️ Discover our magical book clubs!
    
    Join fellow readers on literary adventures and make magical friendships.
    """
    mock_clubs = [
        {
            "id": 1,
            "name": "Dragons & Coffee Book Club",
            "description": "Fantasy lovers who meet every Sunday with coffee and pastries",
            "current_book": "The Name of the Wind",
            "member_count": 45,
            "meeting_day": "Sunday",
            "genre_focus": "fantasy",
            "vibe": "Cozy and magical ✨",
            "next_meeting": "This Sunday at 3 PM"
        },
        {
            "id": 2,
            "name": "Mystery Solvers Society",
            "description": "Detectives at heart who love solving literary puzzles",
            "current_book": "The Thursday Murder Club",
            "member_count": 32,
            "meeting_day": "Wednesday",
            "genre_focus": "mystery",
            "vibe": "Intellectually stimulating 🔍",
            "next_meeting": "Wednesday at 7 PM"
        },
        {
            "id": 3,
            "name": "Sci-Fi Space Explorers",
            "description": "Future-minded readers exploring infinite possibilities",
            "current_book": "Project Hail Mary",
            "member_count": 28,
            "meeting_day": "Friday",
            "genre_focus": "sci_fi",
            "vibe": "Mind-bending and fun 🚀",
            "next_meeting": "Friday at 6 PM"
        }
    ]
    
    # Filter clubs
    filtered_clubs = []
    for club in mock_clubs:
        if not active_only or club.get("is_active", True):
            if not genre_focus or club["genre_focus"] == genre_focus.value:
                filtered_clubs.append(club)
    
    member_perks = []
    if library_card:
        if library_card["level"] == "premium":
            member_perks = ["Early book selections", "Exclusive author events", "Free snacks! 🍪"]
        elif library_card["level"] == "standard":
            member_perks = ["Priority meeting spots", "Digital discussion guides"]
    
    return {
        "active_book_clubs": len(filtered_clubs),
        "clubs": filtered_clubs,
        "joining_benefits": [
            "Make new bookish friends",
            "Discover amazing new books",
            "Engaging discussions",
            "Monthly reading challenges",
            "Author meet-and-greets"
        ],
        "member_perks": member_perks,
        "how_to_join": "Visit any club's page and click 'Join the Adventure!' 📚"
    }

@book_clubs_router.get("/{club_id}")
def get_book_club_details(
    club_id: int = Path(..., title="Club ID", description="The magical identifier of the book club", ge=1),
    include_member_list: bool = Query(False, description="Include member information"),
    library_card = Depends(get_library_card)
):
    """
    🏰 Get detailed information about a specific book club!
    
    Discover what makes each book club special and decide if it's your perfect literary home.
    """
    if club_id not in [1, 2, 3]:
        raise HTTPException(
            status_code=404, 
            detail="🔍 This book club seems to be meeting in a secret location! Try a different ID."
        )
    
    club_details = {
        1: {
            "id": 1,
            "name": "Dragons & Coffee Book Club",
            "description": "A cozy fantasy book club where magic meets caffeine",
            "current_book": {
                "title": "The Name of the Wind",
                "author": "Patrick Rothfuss",
                "progress": "Chapter 12 of 32"
            },
            "meeting_schedule": "Every Sunday at 3 PM",
            "location": "The Cozy Corner (virtual fireplace)",
            "member_count": 45,
            "club_motto": "In coffee we trust, in fantasy we escape! ☕✨",
            "reading_pace": "Relaxed (2-3 chapters per week)",
            "discussion_style": "Friendly and inclusive",
            "special_events": ["Monthly author AMAs", "Fantasy trivia nights", "Coffee tasting sessions"]
        }
    }
    
    club = club_details.get(club_id, {})
    
    if include_member_list and library_card:
        club["recent_members"] = [
            {"username": "DragonReader99", "books_discussed": 15, "favorite_quote": "Words are the true magic! ✨"},
            {"username": "CoffeeMage", "books_discussed": 8, "favorite_quote": "This book changed my life!"},
            {"username": "FantasyFanatic", "books_discussed": 22, "favorite_quote": "Every page is an adventure!"}
        ]
        club["joining_requirements"] = "Just bring your love for fantasy and books! 📚"
    
    return club

@book_clubs_router.post("/", status_code=201)
def create_magical_book_club(
    name: str = Query(..., min_length=5, max_length=100, description="Your club's magical name"),
    description: str = Query(..., min_length=20, description="What makes your club special?"),
    genre_focus: BookGenre = Query(..., description="Primary genre focus"),
    meeting_day: str = Query(..., description="Preferred meeting day"),
    library_card = Depends(get_library_card)
):
    """
    🎉 Start your own magical book club!
    
    Bring together fellow book lovers and create your own literary adventure.
    """
    if not library_card:
        raise HTTPException(
            status_code=401, 
            detail="📋 A library card is required to start a book club! Please get one at the front desk."
        )
    
    club_id = 42  # Mock new club ID
    
    return {
        "club_id": club_id,
        "name": name,
        "description": description,
        "genre_focus": genre_focus.value,
        "meeting_day": meeting_day,
        "status": "🎉 Book club created successfully!",
        "next_steps": [
            "Choose your first book",
            "Invite fellow readers",
            "Schedule your first meeting",
            "Set up your magical meeting space"
        ],
        "founder_perks": [
            "Club customization options",
            "Special founder badge",
            "Priority book selection"
        ],
        "encouragement": "Welcome to the magical world of book club leadership! 📚✨"
    }

# === MEMBER ROUTES ===

members_router = APIRouter(
    prefix="/members",
    tags=["👥 Library Members"],
    dependencies=[Depends(get_library_card)]
)

@members_router.get("/me")
def get_my_reading_profile(library_card = Depends(get_library_card)):
    """
    📊 View your magical reading profile!
    
    Track your reading journey and see how far you've come.
    """
    if not library_card:
        raise HTTPException(
            status_code=401,
            detail="🔐 Please show your library card to access your profile!"
        )
    
    # Mock user profile based on library card level
    profile_data = {
        "username": "BookLover2024",
        "membership_level": library_card["level"],
        "books_read_this_year": 23,
        "current_reading_streak": 15,
        "favorite_genres": ["fantasy", "mystery", "sci_fi"],
        "reading_goal": 30,
        "progress_to_goal": "77% complete! 🎯",
        "achievements": [
            "🏆 Speed Reader (10 books in a month)",
            "🌟 Genre Explorer (read 5+ genres)",
            "📚 Consistent Reader (30-day streak)"
        ],
        "current_book": {
            "title": "The Midnight Library",
            "progress": "45% complete",
            "time_reading_today": "32 minutes"
        },
        "reading_stats": {
            "total_pages_read": 8450,
            "average_rating_given": 4.2,
            "longest_book_completed": "Dune (688 pages)"
        }
    }
    
    # Add level-specific perks
    if library_card["level"] == "premium":
        profile_data["premium_stats"] = {
            "exclusive_books_accessed": 12,
            "author_events_attended": 3,
            "early_access_books": 8
        }
    
    return profile_data

@members_router.get("/{member_id}")
def get_member_public_profile(member_id: int):
    """
    👤 View another member's public reading profile!
    
    Connect with fellow readers and discover new books through their recommendations.
    """
    # Mock public profile
    return {
        "member_id": member_id,
        "username": f"BookWorm{member_id}",
        "membership_since": "January 2023",
        "books_read": 156,
        "public_reviews": 89,
        "favorite_quote": "A reader lives a thousand lives before he dies. The man who never reads lives only one.",
        "currently_reading": "The Seven Husbands of Evelyn Hugo",
        "recently_finished": [
            {"title": "Atomic Habits", "rating": 5, "review": "Life-changing! 🌟"},
            {"title": "Dune", "rating": 4, "review": "Epic space opera!"},
            {"title": "The Thursday Murder Club", "rating": 4, "review": "Clever and charming mystery"}
        ],
        "reading_personality": "The Adventurous Explorer - loves trying new genres!",
        "book_clubs": ["Dragons & Coffee Book Club", "Sci-Fi Space Explorers"]
    }

# === SPECIAL FEATURES ===

@app.get("/daily-recommendation")
def get_daily_book_magic(
    mood: Optional[str] = Query(None, description="How are you feeling today?"),
    available_time: Optional[int] = Query(None, description="Minutes available for reading", ge=5, le=480),
    library_card = Depends(get_library_card)
):
    """
    🔮 Get your personalized daily book recommendation!
    
    Our magical recommendation system considers your mood and available time.
    """
    
    # Mood-based recommendations
    mood_books = {
        "happy": {"title": "Beach Read", "reason": "Perfect for maintaining those good vibes! ☀️"},
        "sad": {"title": "The Midnight Library", "reason": "A gentle, hopeful story to lift your spirits 🌟"},
        "curious": {"title": "Sapiens", "reason": "Feed that curious mind with fascinating insights! 🧠"},
        "adventurous": {"title": "The Name of the Wind", "reason": "Epic adventures await! ⚔️"},
        "romantic": {"title": "The Seven Husbands of Evelyn Hugo", "reason": "Swoon-worthy romance! 💕"},
        "mysterious": {"title": "The Silent Patient", "reason": "A puzzle that will keep you guessing! 🔍"}
    }
    
    recommendation = mood_books.get(mood, {"title": "Atomic Habits", "reason": "A great choice for any mood! 📚"})
    
    # Time-based reading suggestions
    time_suggestion = "Perfect for a long reading session!"
    if available_time:
        if available_time <= 15:
            time_suggestion = "Perfect for a quick chapter! ⚡"
        elif available_time <= 60:
            time_suggestion = "Great for a solid reading session! 📖"
        elif available_time >= 120:
            time_suggestion = "Time for a deep reading dive! 🌊"
    
    return {
        "todays_magic_book": recommendation["title"],
        "why_this_book": recommendation["reason"],
        "reading_time_note": time_suggestion,
        "your_mood": mood or "mysterious (since you didn't tell us! 😊)",
        "magical_reading_tip": "Find a cozy spot, grab your favorite drink, and let the magic begin! ✨",
        "bonus_feature": "Premium members get personalized bookmarks!" if library_card and library_card["level"] == "premium" else None
    }

# Include all the routers
app.include_router(book_clubs_router)
app.include_router(members_router)

# === PRACTICE EXERCISE SOLUTION ===

# Enhanced Library Management System
reading_lists_router = APIRouter(
    prefix="/reading-lists",
    tags=["📝 Reading Lists"],
    responses={404: {"description": "Reading list not found"}}
)

@reading_lists_router.get("/")
def get_curated_reading_lists(
    theme: Optional[str] = Query(None, description="List theme (e.g., 'summer', 'productivity', 'escape')"),
    difficulty: Optional[str] = Query(None, description="Reading difficulty (easy, medium, challenging)"),
    library_card = Depends(get_library_card)
):
    """
    📋 Discover our magical curated reading lists!
    
    Perfect for when you want a guided reading adventure.
    """
    mock_lists = [
        {
            "id": 1,
            "title": "🌞 Perfect Summer Escapes",
            "description": "Light, breezy reads perfect for beach days and hammocks",
            "books": ["Beach Read", "The Seven Husbands of Evelyn Hugo", "Malibu Rising"],
            "estimated_reading_time": "6-8 weeks",
            "difficulty": "easy",
            "curator": "The Beach Reading Expert"
        },
        {
            "id": 2,
            "title": "🧠 Mind-Expanding Adventures",
            "description": "Books that will change how you see the world",
            "books": ["Sapiens", "Thinking Fast and Slow", "The Power of Now"],
            "estimated_reading_time": "10-12 weeks",
            "difficulty": "challenging",
            "curator": "The Philosophy Professor"
        },
        {
            "id": 3,
            "title": "🏰 Epic Fantasy Journeys",
            "description": "Immersive fantasy worlds for the ultimate escape",
            "books": ["The Name of the Wind", "The Way of Kings", "The Fifth Season"],
            "estimated_reading_time": "12-15 weeks",
            "difficulty": "medium",
            "curator": "The Dragon Whisperer"
        }
    ]
    
    return {
        "curated_lists": mock_lists,
        "total_lists": len(mock_lists),
        "personalization_note": "Premium members get AI-powered personalized lists!" if library_card and library_card["level"] == "premium" else "Create an account for personalized recommendations!",
        "how_to_use": "Pick a list that matches your mood and follow the magical reading journey! ✨"
    }

@reading_lists_router.post("/{list_id}/join")
def join_reading_challenge(
    list_id: int,
    target_completion_weeks: int = Query(8, description="How many weeks to complete the list?", ge=1, le=52),
    library_card = Depends(get_library_card)
):
    """
    🚀 Join a reading challenge and track your progress!
    
    Turn reading into an adventure with goals and achievements.
    """
    if not library_card:
        raise HTTPException(
            status_code=401,
            detail="📋 A library card is required to join challenges!"
        )
    
    return {
        "challenge_id": f"CHALLENGE_{list_id}_{uuid.uuid4().hex[:8]}",
        "status": "🎉 Challenge accepted!",
        "reading_list": f"Reading List #{list_id}",
        "target_weeks": target_completion_weeks,
        "books_per_week": 1.5,  # Mock calculation
        "start_date": date.today().isoformat(),
        "estimated_completion": "2024-03-15",
        "motivation": "You've got this! Every page is progress! 📚✨",
        "tracking_features": [
            "Weekly progress emails",
            "Achievement badges",
            "Community support",
            "Reading streak tracking"
        ],
        "reward": "Complete the challenge to earn a special 'Reading Warrior' badge! 🏆"
    }

app.include_router(reading_lists_router)

if __name__ == "__main__":
    import uvicorn
    print("📚 Opening the Magical Digital Library...")
    print("✨ Where every book is an adventure waiting to happen!")
    uvicorn.run(app, host="0.0.0.0", port=8000) 