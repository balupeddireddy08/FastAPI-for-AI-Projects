from fastapi import FastAPI, Path, Query, Body, Depends, Security, HTTPException, status, Header
from fastapi.openapi.utils import get_openapi
from fastapi.security import APIKeyHeader, OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, EmailStr, validator, HttpUrl
from typing import List, Optional, Dict, Union
from enum import Enum
import uuid
from datetime import datetime, date

# Custom OpenAPI schema for our AI Assistant Marketplace
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="🤖 AI Assistant Marketplace - The Future of Digital Assistance",
        version="3.0.0",
        description="""
        Welcome to the **AI Assistant Marketplace** - where cutting-edge artificial intelligence meets human creativity! 🚀
        
        ## 🌟 What You Can Do Here
        
        Our marketplace connects you with the most advanced AI assistants, each specialized in different areas:
        
        * 🎨 **Creative Assistants**: Art generation, writing, music composition
        * 🧠 **Analytical Assistants**: Data analysis, research, problem-solving  
        * 💼 **Business Assistants**: Meeting scheduling, email management, reporting
        * 🎓 **Educational Assistants**: Tutoring, language learning, skill development
        * 🏠 **Personal Assistants**: Life organization, health tracking, entertainment
        
        ## 🔥 Key Features
        
        - **Instant AI Access**: Connect with any assistant in seconds
        - **Custom Training**: Train assistants on your specific needs
        - **Real-time Collaboration**: Work with AI assistants in real-time
        - **Usage Analytics**: Track performance and optimize workflows
        - **Marketplace Integration**: Buy, sell, and share AI assistant configurations
        
        ## 🛡️ Security & Privacy
        
        All interactions are encrypted and privacy-focused. Your data stays yours!
        
        ## 📞 Support
        
        Need help? Contact our support team at support@aimarketplace.com or visit our help center.
        
        ---
        
        *Built with ❤️ using FastAPI - Making AI accessible to everyone!*
        """,
        routes=app.routes,
        contact={
            "name": "AI Marketplace Support Team",
            "url": "https://aimarketplace.com/support",
            "email": "support@aimarketplace.com",
        },
        license_info={
            "name": "MIT License",
            "url": "https://opensource.org/licenses/MIT",
        },
        servers=[
            {
                "url": "https://api.aimarketplace.com",
                "description": "Production server"
            },
            {
                "url": "https://staging-api.aimarketplace.com", 
                "description": "Staging server"
            },
            {
                "url": "http://localhost:8000",
                "description": "Development server"
            }
        ]
    )
    
    # Add custom metadata
    openapi_schema["info"]["x-logo"] = {
        "url": "https://aimarketplace.com/logo.png"
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

# Initialize our AI Assistant Marketplace API
app = FastAPI(
    title="🤖 AI Assistant Marketplace",
    description="The most advanced platform for discovering, creating, and deploying AI assistants",
    version="3.0.0",
    docs_url="/docs",  # Swagger UI
    redoc_url="/redoc",  # ReDoc
    openapi_url="/openapi.json",  # OpenAPI schema
    openapi_tags=[
        {
            "name": "🏠 Home",
            "description": "Welcome and platform overview"
        },
        {
            "name": "🤖 AI Assistants",
            "description": "Discover, create, and manage AI assistants",
            "externalDocs": {
                "description": "AI Assistant Guide",
                "url": "https://aimarketplace.com/docs/assistants"
            }
        },
        {
            "name": "💬 Conversations",
            "description": "Chat and interact with AI assistants"
        },
        {
            "name": "👤 Users",
            "description": "User management and profiles"
        },
        {
            "name": "🏪 Marketplace",
            "description": "Buy, sell, and discover AI assistant templates"
        },
        {
            "name": "📊 Analytics",
            "description": "Usage statistics and performance metrics"
        },
        {
            "name": "🔧 Admin",
            "description": "Administrative endpoints (requires admin access)"
        }
    ]
)

# Custom OpenAPI schema
app.openapi = custom_openapi

# === ENUMS FOR BETTER DOCUMENTATION ===

class AISpecialty(str, Enum):
    """AI Assistant specialization areas"""
    CREATIVE = "creative"
    ANALYTICAL = "analytical"
    BUSINESS = "business"
    EDUCATIONAL = "educational"
    PERSONAL = "personal"
    TECHNICAL = "technical"
    HEALTHCARE = "healthcare"
    ENTERTAINMENT = "entertainment"

class ConversationStatus(str, Enum):
    """Status of conversations with AI assistants"""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"

class SubscriptionTier(str, Enum):
    """Available subscription tiers"""
    FREE = "free"
    BASIC = "basic"
    PRO = "pro"
    ENTERPRISE = "enterprise"

class AIModel(str, Enum):
    """Available AI model types"""
    GPT4 = "gpt-4"
    GPT35_TURBO = "gpt-3.5-turbo"
    CLAUDE = "claude-3"
    GEMINI = "gemini-pro"
    CUSTOM = "custom"

# === REQUEST MODELS ===

class AIAssistantCreate(BaseModel):
    """Create a new AI assistant with specific capabilities and personality"""
    
    name: str = Field(
        ..., 
        min_length=1, 
        max_length=100,
        description="Name of your AI assistant",
        example="Creative Writing Companion"
    )
    description: str = Field(
        ..., 
        min_length=10, 
        max_length=1000,
        description="Detailed description of what this assistant does",
        example="An AI assistant specialized in creative writing, poetry, and storytelling. Helps with plot development, character creation, and writing style improvement."
    )
    specialty: AISpecialty = Field(
        ...,
        description="Primary specialization area",
        example=AISpecialty.CREATIVE
    )
    personality: str = Field(
        ...,
        min_length=10,
        max_length=500,
        description="Personality traits and communication style",
        example="Friendly, encouraging, and imaginative. Uses creative metaphors and provides constructive feedback with enthusiasm."
    )
    ai_model: AIModel = Field(
        AIModel.GPT35_TURBO,
        description="Underlying AI model to use",
        example=AIModel.GPT4
    )
    is_public: bool = Field(
        True,
        description="Whether this assistant is available to other users",
        example=True
    )
    price_per_session: Optional[float] = Field(
        None,
        ge=0,
        le=100,
        description="Price per conversation session (if selling)",
        example=2.99
    )
    tags: List[str] = Field(
        [],
        max_items=10,
        description="Tags for discoverability",
        example=["writing", "creative", "storytelling", "poetry"]
    )
    
    @validator('tags')
    def validate_tags(cls, v):
        """Ensure tags are clean and not duplicated"""
        if len(v) > 10:
            raise ValueError('Maximum 10 tags allowed')
        cleaned_tags = []
        for tag in v:
            clean_tag = tag.strip().lower()
            if clean_tag and clean_tag not in cleaned_tags and len(clean_tag) <= 30:
                cleaned_tags.append(clean_tag)
        return cleaned_tags
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Python Coding Mentor",
                "description": "An expert Python developer assistant that helps with code review, debugging, optimization, and learning advanced Python concepts.",
                "specialty": "technical",
                "personality": "Patient, detailed, and encouraging. Explains complex concepts in simple terms and provides practical examples.",
                "ai_model": "gpt-4",
                "is_public": True,
                "price_per_session": 4.99,
                "tags": ["python", "programming", "debugging", "code-review", "learning"]
            }
        }

class ConversationStart(BaseModel):
    """Start a new conversation with an AI assistant"""
    
    assistant_id: int = Field(
        ...,
        ge=1,
        description="ID of the AI assistant to chat with",
        example=123
    )
    initial_message: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Your first message to the assistant",
        example="Hi! I'm working on a fantasy novel and need help developing my main character. Can you help me brainstorm some unique personality traits?"
    )
    context: Optional[str] = Field(
        None,
        max_length=1000,
        description="Additional context or background information",
        example="I'm writing a fantasy novel set in a steampunk world with magical elements. The main character is a young inventor."
    )
    session_budget: Optional[float] = Field(
        None,
        ge=0,
        le=50,
        description="Maximum amount willing to spend on this session",
        example=10.00
    )
    
    class Config:
        schema_extra = {
            "example": {
                "assistant_id": 456,
                "initial_message": "I need help analyzing this dataset to find patterns in customer behavior. Can you guide me through the process?",
                "context": "I have a CSV file with customer purchase data including demographics, purchase history, and preferences.",
                "session_budget": 15.00
            }
        }

class MessageSend(BaseModel):
    """Send a message in an ongoing conversation"""
    
    content: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Your message content",
        example="That's really helpful! Can you show me how to implement this in Python?"
    )
    include_files: Optional[List[str]] = Field(
        None,
        description="File IDs to include with this message",
        example=["file_123", "file_456"]
    )
    
    @validator('content')
    def validate_content(cls, v):
        """Clean and validate message content"""
        cleaned = v.strip()
        if not cleaned:
            raise ValueError('Message content cannot be empty')
        return cleaned

class UserRegistration(BaseModel):
    """Register a new user account"""
    
    username: str = Field(
        ...,
        min_length=3,
        max_length=30,
        description="Unique username",
        example="ai_enthusiast_2024"
    )
    email: EmailStr = Field(
        ...,
        description="Email address",
        example="user@example.com"
    )
    password: str = Field(
        ...,
        min_length=8,
        description="Strong password",
        example="SecurePassword123!"
    )
    full_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Full name",
        example="Alex Johnson"
    )
    subscription_tier: SubscriptionTier = Field(
        SubscriptionTier.FREE,
        description="Initial subscription tier",
        example=SubscriptionTier.BASIC
    )
    
    @validator('username')
    def username_alphanumeric(cls, v):
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Username can only contain letters, numbers, underscores, and hyphens')
        return v.lower()
    
    @validator('password')
    def password_strength(cls, v):
        """Ensure password meets security requirements"""
        checks = [
            (any(c.isdigit() for c in v), "at least one number"),
            (any(c.isupper() for c in v), "at least one uppercase letter"),
            (any(c.islower() for c in v), "at least one lowercase letter"),
            (any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in v), "at least one special character")
        ]
        
        failed_checks = [msg for passed, msg in checks if not passed]
        if failed_checks:
            raise ValueError(f"Password must contain {', '.join(failed_checks)}")
        return v

# === RESPONSE MODELS ===

class UserProfile(BaseModel):
    """User profile information (safe for public viewing)"""
    
    id: int = Field(..., description="Unique user ID", example=12345)
    username: str = Field(..., description="Username", example="ai_enthusiast_2024")
    full_name: str = Field(..., description="Full name", example="Alex Johnson")
    subscription_tier: SubscriptionTier = Field(..., description="Current subscription", example=SubscriptionTier.PRO)
    joined_date: date = Field(..., description="Account creation date", example="2024-01-15")
    assistants_created: int = Field(..., description="Number of assistants created", example=5)
    conversations_count: int = Field(..., description="Total conversations", example=128)
    rating: float = Field(..., description="Average rating as assistant creator", example=4.7)
    verified_creator: bool = Field(..., description="Verified assistant creator status", example=True)
    
    class Config:
        schema_extra = {
            "example": {
                "id": 98765,
                "username": "creative_ai_master",
                "full_name": "Sarah Williams",
                "subscription_tier": "pro",
                "joined_date": "2023-08-20",
                "assistants_created": 12,
                "conversations_count": 543,
                "rating": 4.9,
                "verified_creator": True
            }
        }

class AIAssistantResponse(BaseModel):
    """Complete AI assistant information"""
    
    id: int = Field(..., description="Unique assistant ID", example=123)
    name: str = Field(..., description="Assistant name", example="Creative Writing Companion")
    description: str = Field(..., description="What this assistant does")
    specialty: AISpecialty = Field(..., description="Primary specialization")
    personality: str = Field(..., description="Communication style and personality")
    creator: UserProfile = Field(..., description="Assistant creator information")
    ai_model: AIModel = Field(..., description="Underlying AI model")
    created_at: datetime = Field(..., description="Creation timestamp")
    is_public: bool = Field(..., description="Public availability")
    price_per_session: Optional[float] = Field(None, description="Session price")
    tags: List[str] = Field(..., description="Searchable tags")
    rating: float = Field(..., description="Average user rating", example=4.5)
    total_conversations: int = Field(..., description="Total usage count", example=1250)
    active_users: int = Field(..., description="Active users this month", example=89)
    
    class Config:
        schema_extra = {
            "example": {
                "id": 789,
                "name": "Data Science Mentor",
                "description": "Expert assistant for data analysis, machine learning, and statistical modeling. Helps with everything from data cleaning to advanced ML algorithms.",
                "specialty": "analytical",
                "personality": "Methodical, thorough, and encouraging. Breaks down complex problems into manageable steps.",
                "ai_model": "gpt-4",
                "created_at": "2024-01-10T14:30:00Z",
                "is_public": True,
                "price_per_session": 6.99,
                "tags": ["data-science", "machine-learning", "python", "statistics"],
                "rating": 4.8,
                "total_conversations": 2150,
                "active_users": 156
            }
        }

class ConversationResponse(BaseModel):
    """Active conversation details"""
    
    id: int = Field(..., description="Conversation ID", example=456)
    assistant: AIAssistantResponse = Field(..., description="Assistant information")
    status: ConversationStatus = Field(..., description="Current status")
    started_at: datetime = Field(..., description="Start time")
    last_activity: datetime = Field(..., description="Last message time")
    message_count: int = Field(..., description="Total messages exchanged", example=15)
    cost_so_far: float = Field(..., description="Session cost so far", example=3.45)
    estimated_remaining_budget: Optional[float] = Field(None, description="Remaining budget")

class MessageResponse(BaseModel):
    """AI assistant message response"""
    
    id: int = Field(..., description="Message ID", example=789)
    conversation_id: int = Field(..., description="Parent conversation ID", example=456)
    content: str = Field(..., description="Message content")
    sender: str = Field(..., description="Message sender", example="assistant")
    timestamp: datetime = Field(..., description="Message timestamp")
    tokens_used: int = Field(..., description="AI tokens consumed", example=150)
    cost: float = Field(..., description="Message cost", example=0.23)
    
    class Config:
        schema_extra = {
            "example": {
                "id": 12345,
                "conversation_id": 456,
                "content": "Great question! Let me help you develop that character. Based on your steampunk fantasy setting, here are some unique personality traits to consider...",
                "sender": "assistant",
                "timestamp": "2024-01-15T16:45:30Z",
                "tokens_used": 180,
                "cost": 0.27
            }
        }

class MarketplaceStats(BaseModel):
    """Marketplace statistics and insights"""
    
    total_assistants: int = Field(..., description="Total assistants available", example=1250)
    active_conversations: int = Field(..., description="Currently active conversations", example=89)
    total_users: int = Field(..., description="Registered users", example=45000)
    popular_specialties: List[Dict[str, Union[str, int]]] = Field(
        ...,
        description="Most popular assistant specialties"
    )
    trending_assistants: List[AIAssistantResponse] = Field(
        ...,
        description="Currently trending assistants"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "total_assistants": 1847,
                "active_conversations": 156,
                "total_users": 67834,
                "popular_specialties": [
                    {"specialty": "creative", "count": 245},
                    {"specialty": "technical", "count": 198},
                    {"specialty": "business", "count": 156}
                ]
            }
        }

# === DEPENDENCY FUNCTIONS FOR DOCUMENTATION ===

def get_api_key(x_api_key: Optional[str] = Header(None, description="Your API key for authentication")):
    """
    Validate API key for accessing premium features.
    
    Get your API key from: https://aimarketplace.com/settings/api-keys
    """
    if x_api_key is None:
        return {"tier": "free", "rate_limit": 10}
    
    # Mock API key validation
    if x_api_key == "demo_key_12345":
        return {"tier": "pro", "rate_limit": 1000, "user_id": 12345}
    elif x_api_key.startswith("basic_"):
        return {"tier": "basic", "rate_limit": 100, "user_id": 67890}
    else:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key. Get yours at https://aimarketplace.com/settings/api-keys"
        )

def get_current_user(api_key_info = Depends(get_api_key)):
    """Get current authenticated user information"""
    if api_key_info["tier"] == "free":
        return None
    return {
        "id": api_key_info["user_id"],
        "tier": api_key_info["tier"],
        "rate_limit": api_key_info["rate_limit"]
    }

# === MAIN ENDPOINTS ===

@app.get(
    "/",
    tags=["🏠 Home"],
    summary="Welcome to AI Assistant Marketplace",
    description="Get platform overview, featured assistants, and quick start information",
    response_description="Platform welcome information with stats and featured content"
)
def marketplace_home():
    """
    🏠 **Welcome to the AI Assistant Marketplace!**
    
    The premier destination for discovering, creating, and deploying AI assistants.
    
    ## 🚀 Quick Start
    1. Browse available assistants in the marketplace
    2. Start a conversation with any assistant
    3. Create your own custom assistants
    4. Share and monetize your creations
    
    ## 📈 Platform Stats
    - Over 1,500 specialized AI assistants
    - 50,000+ active users worldwide
    - 1M+ conversations completed
    - 99.9% uptime reliability
    """
    return {
        "message": "🤖 Welcome to the AI Assistant Marketplace!",
        "tagline": "Where AI meets human creativity and innovation",
        "platform_stats": {
            "total_assistants": 1547,
            "active_users": 12340,
            "conversations_today": 8920,
            "uptime": "99.97%"
        },
        "featured_assistants": [
            {"id": 123, "name": "Creative Writing Companion", "rating": 4.9},
            {"id": 456, "name": "Data Science Mentor", "rating": 4.8},
            {"id": 789, "name": "Business Strategy Advisor", "rating": 4.7}
        ],
        "quick_links": {
            "browse_assistants": "/assistants/",
            "create_assistant": "/assistants/create",
            "documentation": "/docs",
            "support": "https://aimarketplace.com/support"
        }
    }

@app.get(
    "/assistants/",
    response_model=List[AIAssistantResponse],
    tags=["🤖 AI Assistants"],
    summary="Browse available AI assistants",
    description="Discover AI assistants by specialty, rating, price, and more",
    response_description="List of AI assistants matching your criteria"
)
def browse_assistants(
    specialty: Optional[AISpecialty] = Query(
        None,
        description="Filter by assistant specialty",
        example=AISpecialty.CREATIVE
    ),
    min_rating: float = Query(
        0.0,
        ge=0.0,
        le=5.0,
        description="Minimum average rating",
        example=4.0
    ),
    max_price: Optional[float] = Query(
        None,
        ge=0,
        description="Maximum price per session",
        example=10.00
    ),
    tags: Optional[str] = Query(
        None,
        description="Comma-separated tags to search for",
        example="writing,creative,storytelling"
    ),
    sort_by: str = Query(
        "rating",
        description="Sort results by: rating, price, popularity, newest",
        example="rating"
    ),
    limit: int = Query(
        20,
        ge=1,
        le=100,
        description="Maximum number of results",
        example=20
    ),
    api_key = Depends(get_api_key)
):
    """
    🔍 **Discover Amazing AI Assistants!**
    
    Browse our extensive collection of specialized AI assistants. Each assistant
    is expertly crafted for specific tasks and domains.
    
    ### 🎯 Popular Specialties:
    - **Creative**: Writing, art, music, design
    - **Analytical**: Data analysis, research, problem-solving
    - **Business**: Strategy, marketing, operations
    - **Educational**: Tutoring, language learning
    - **Technical**: Programming, engineering, IT support
    
    ### 💡 Pro Tips:
    - Use specific tags for better results
    - Higher-rated assistants typically provide better experiences
    - Try free assistants first to find your preferences
    - Check the assistant's conversation history for insights
    """
    
    # Mock assistant data
    mock_assistants = [
        {
            "id": 123,
            "name": "Creative Writing Companion",
            "description": "Expert assistant for creative writing, storytelling, and literary development",
            "specialty": "creative",
            "personality": "Encouraging, imaginative, and detail-oriented",
            "creator": {
                "id": 456,
                "username": "literary_master",
                "full_name": "Emma Thompson",
                "subscription_tier": "pro",
                "joined_date": "2023-05-15",
                "assistants_created": 8,
                "conversations_count": 342,
                "rating": 4.9,
                "verified_creator": True
            },
            "ai_model": "gpt-4",
            "created_at": "2024-01-10T14:30:00Z",
            "is_public": True,
            "price_per_session": 4.99,
            "tags": ["writing", "creative", "storytelling", "poetry"],
            "rating": 4.9,
            "total_conversations": 1250,
            "active_users": 89
        }
    ]
    
    # Apply filters (simplified for demo)
    filtered_assistants = mock_assistants
    
    if specialty:
        filtered_assistants = [a for a in filtered_assistants if a["specialty"] == specialty.value]
    
    if api_key["tier"] == "free":
        # Free tier gets limited results
        filtered_assistants = filtered_assistants[:5]
    
    return filtered_assistants[:limit]

@app.get(
    "/assistants/{assistant_id}",
    response_model=AIAssistantResponse,
    tags=["🤖 AI Assistants"],
    summary="Get detailed assistant information",
    description="Retrieve comprehensive details about a specific AI assistant",
    responses={
        200: {
            "description": "Assistant details retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": 123,
                        "name": "Creative Writing Companion",
                        "description": "Expert assistant for creative writing and storytelling",
                        "specialty": "creative",
                        "rating": 4.9,
                        "total_conversations": 1250
                    }
                }
            }
        },
        404: {
            "description": "Assistant not found",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "🤖 Assistant not found. It might be in another dimension!"
                    }
                }
            }
        }
    }
)
def get_assistant_details(
    assistant_id: int = Path(
        ...,
        ge=1,
        description="Unique assistant identifier",
        example=123
    ),
    include_stats: bool = Query(
        True,
        description="Include usage statistics and performance metrics"
    ),
    api_key = Depends(get_api_key)
):
    """
    🤖 **Get Complete Assistant Information**
    
    Retrieve detailed information about any AI assistant including:
    
    - **Capabilities**: What the assistant specializes in
    - **Personality**: Communication style and approach  
    - **Performance**: Ratings, usage stats, and user feedback
    - **Pricing**: Cost per session and subscription options
    - **Creator**: Information about who built this assistant
    
    ### 📊 Included Metrics:
    - Average rating from users
    - Total conversation count
    - Active users this month
    - Response time performance
    - Success rate for task completion
    """
    
    # Mock assistant lookup
    if assistant_id not in [123, 456, 789]:
        raise HTTPException(
            status_code=404,
            detail=f"🤖 Assistant #{assistant_id} not found. It might be in another dimension of the AI multiverse!"
        )
    
    mock_assistant = {
        "id": assistant_id,
        "name": "Creative Writing Companion",
        "description": "An expert AI assistant specialized in creative writing, storytelling, and literary development. Helps with plot creation, character development, dialogue writing, and style improvement.",
        "specialty": "creative",
        "personality": "Encouraging, imaginative, and detail-oriented. Provides constructive feedback with enthusiasm and creativity.",
        "creator": {
            "id": 456,
            "username": "literary_master",
            "full_name": "Emma Thompson",
            "subscription_tier": "pro",
            "joined_date": "2023-05-15",
            "assistants_created": 8,
            "conversations_count": 342,
            "rating": 4.9,
            "verified_creator": True
        },
        "ai_model": "gpt-4",
        "created_at": "2024-01-10T14:30:00Z",
        "is_public": True,
        "price_per_session": 4.99,
        "tags": ["writing", "creative", "storytelling", "poetry", "literature"],
        "rating": 4.9,
        "total_conversations": 1250,
        "active_users": 89
    }
    
    return mock_assistant

@app.post(
    "/assistants/",
    response_model=AIAssistantResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["🤖 AI Assistants"],
    summary="Create a new AI assistant",
    description="Design and deploy your own custom AI assistant with specific capabilities",
    response_description="Newly created assistant details"
)
def create_ai_assistant(
    assistant_data: AIAssistantCreate = Body(
        ...,
        description="Assistant configuration and personality definition"
    ),
    current_user = Depends(get_current_user)
):
    """
    🎨 **Create Your Own AI Assistant!**
    
    Bring your vision to life by creating a custom AI assistant tailored to your needs.
    
    ### 🛠️ What You Can Customize:
    - **Personality**: Define how your assistant communicates
    - **Expertise**: Choose specialization areas and knowledge domains  
    - **Behavior**: Set response style, tone, and approach
    - **Pricing**: Decide if it's free or premium (and set rates)
    - **Visibility**: Public marketplace or private use only
    
    ### 💡 Creation Tips:
    - Be specific about the assistant's role and capabilities
    - Define clear personality traits for consistent interactions
    - Use relevant tags to help users discover your assistant
    - Test thoroughly before making it public
    - Consider your target audience when setting pricing
    
    ### 🚀 After Creation:
    Your assistant will be available immediately for testing. Public assistants
    go through a brief review process to ensure quality standards.
    """
    
    if current_user is None:
        raise HTTPException(
            status_code=401,
            detail="🔐 Authentication required to create assistants. Please provide a valid API key."
        )
    
    # Mock assistant creation
    new_assistant_id = 99999
    
    mock_creator = {
        "id": current_user["id"],
        "username": "current_user",
        "full_name": "Current User",
        "subscription_tier": current_user["tier"],
        "joined_date": "2024-01-01",
        "assistants_created": 1,
        "conversations_count": 0,
        "rating": 5.0,
        "verified_creator": False
    }
    
    new_assistant = {
        "id": new_assistant_id,
        "name": assistant_data.name,
        "description": assistant_data.description,
        "specialty": assistant_data.specialty.value,
        "personality": assistant_data.personality,
        "creator": mock_creator,
        "ai_model": assistant_data.ai_model.value,
        "created_at": datetime.now(),
        "is_public": assistant_data.is_public,
        "price_per_session": assistant_data.price_per_session,
        "tags": assistant_data.tags,
        "rating": 5.0,  # New assistants start with perfect rating
        "total_conversations": 0,
        "active_users": 0
    }
    
    return new_assistant

@app.post(
    "/conversations/",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["💬 Conversations"],
    summary="Start a new conversation",
    description="Begin chatting with an AI assistant",
    response_description="New conversation details with first message response"
)
def start_conversation(
    conversation_data: ConversationStart = Body(...),
    current_user = Depends(get_current_user)
):
    """
    💬 **Start Chatting with an AI Assistant!**
    
    Begin a new conversation session with any available AI assistant.
    
    ### 🎯 How It Works:
    1. Choose your assistant based on specialty and needs
    2. Provide initial context or question
    3. Set optional budget limits for paid assistants
    4. Start receiving intelligent, personalized responses
    
    ### 💰 Pricing:
    - **Free assistants**: No cost for basic interactions
    - **Premium assistants**: Pay-per-message or session rates
    - **Budget controls**: Set spending limits to avoid surprises
    
    ### 🔧 Pro Features:
    - File attachments for context
    - Conversation history and bookmarking
    - Export chat transcripts
    - Real-time collaboration with team members
    """
    
    if current_user is None:
        raise HTTPException(
            status_code=401,
            detail="🔐 Please authenticate to start conversations"
        )
    
    # Mock conversation creation
    mock_conversation = {
        "id": 78910,
        "assistant": {
            "id": conversation_data.assistant_id,
            "name": "Creative Writing Companion",
            "description": "Expert writing assistant",
            "specialty": "creative",
            "personality": "Encouraging and imaginative",
            "creator": {
                "id": 456,
                "username": "literary_master",
                "full_name": "Emma Thompson",
                "subscription_tier": "pro",
                "joined_date": "2023-05-15",
                "assistants_created": 8,
                "conversations_count": 342,
                "rating": 4.9,
                "verified_creator": True
            },
            "ai_model": "gpt-4",
            "created_at": "2024-01-10T14:30:00Z",
            "is_public": True,
            "price_per_session": 4.99,
            "tags": ["writing", "creative"],
            "rating": 4.9,
            "total_conversations": 1251,
            "active_users": 90
        },
        "status": "active",
        "started_at": datetime.now(),
        "last_activity": datetime.now(),
        "message_count": 1,
        "cost_so_far": 0.50,
        "estimated_remaining_budget": conversation_data.session_budget - 0.50 if conversation_data.session_budget else None
    }
    
    return mock_conversation

# Additional endpoints would continue...

if __name__ == "__main__":
    import uvicorn
    print("🤖 Starting AI Assistant Marketplace...")
    print("📚 Documentation available at http://localhost:8000/docs")
    print("🎯 ReDoc available at http://localhost:8000/redoc")
    uvicorn.run(app, host="0.0.0.0", port=8000) 