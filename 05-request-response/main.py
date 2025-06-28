from fastapi import FastAPI, HTTPException, Path, Query, Body, Form, File, UploadFile, status
from fastapi.responses import JSONResponse, HTMLResponse, Response
from pydantic import BaseModel, Field, EmailStr, validator, HttpUrl
from typing import List, Optional, Dict, Union
from datetime import datetime, date
import uuid
import hashlib

app = FastAPI(
    title="📱 InstaConnect - Social Media Platform",
    description="The most engaging social media platform! Share posts, connect with friends, and build your digital community.",
    version="1.0.0"
)

# === ENUMS FOR BETTER VALIDATION ===
from enum import Enum

class PostType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    STORY = "story"
    POLL = "poll"

class ReactionType(str, Enum):
    LIKE = "like"
    LOVE = "love"
    LAUGH = "laugh"
    WOW = "wow"
    ANGRY = "angry"
    CARE = "care"

class PrivacyLevel(str, Enum):
    PUBLIC = "public"
    FRIENDS = "friends"
    PRIVATE = "private"

# === REQUEST MODELS (What users send to us) ===

class UserSignup(BaseModel):
    username: str = Field(..., min_length=3, max_length=30, description="Your unique username")
    email: EmailStr = Field(..., description="Your email address")
    password: str = Field(..., min_length=8, description="Strong password required")
    full_name: str = Field(..., min_length=1, max_length=100, description="Your display name")
    bio: Optional[str] = Field(None, max_length=500, description="Tell us about yourself!")
    date_of_birth: date = Field(..., description="Your birthday")
    
    @validator('username')
    def username_alphanumeric(cls, v):
        if not v.replace('_', '').isalnum():
            raise ValueError('Username can only contain letters, numbers, and underscores')
        return v.lower()
    
    @validator('password')
    def password_strength(cls, v):
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one number')
        if not any(char.isupper() for char in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(char in "!@#$%^&*()_+-=[]{}|;:,.<>?" for char in v):
            raise ValueError('Password must contain at least one special character')
        return v
    
    @validator('date_of_birth')
    def age_check(cls, v):
        today = date.today()
        age = today.year - v.year - ((today.month, today.day) < (v.month, v.day))
        if age < 13:
            raise ValueError('You must be at least 13 years old to join InstaConnect')
        return v

class PostCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=2200, description="What's on your mind?")
    post_type: PostType = Field(PostType.TEXT, description="Type of post you're sharing")
    privacy: PrivacyLevel = Field(PrivacyLevel.PUBLIC, description="Who can see this post?")
    tags: List[str] = Field([], description="Tag friends or topics")
    location: Optional[str] = Field(None, max_length=100, description="Where are you posting from?")
    media_url: Optional[HttpUrl] = Field(None, description="Link to image or video")
    
    @validator('content')
    def content_not_empty_after_strip(cls, v):
        if not v.strip():
            raise ValueError('Post content cannot be empty or just whitespace')
        return v.strip()
    
    @validator('tags')
    def validate_tags(cls, v):
        if len(v) > 10:
            raise ValueError('Maximum 10 tags allowed per post')
        for tag in v:
            if len(tag) > 50:
                raise ValueError('Each tag must be 50 characters or less')
        return [tag.lower().strip() for tag in v]

class CommentCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=500, description="Share your thoughts")
    parent_comment_id: Optional[int] = Field(None, description="Reply to another comment")
    
    @validator('content')
    def content_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Comment cannot be empty')
        return v.strip()

class ProfileUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=1, max_length=100)
    bio: Optional[str] = Field(None, max_length=500)
    location: Optional[str] = Field(None, max_length=100)
    website: Optional[HttpUrl] = None
    privacy_settings: Optional[Dict[str, bool]] = None
    
    class Config:
        schema_extra = {
            "example": {
                "full_name": "Alex Johnson",
                "bio": "📸 Photography enthusiast | 🌍 Travel lover | ☕ Coffee addict",
                "location": "San Francisco, CA",
                "website": "https://alexjohnson.photography",
                "privacy_settings": {
                    "show_email": False,
                    "show_phone": False,
                    "allow_messages_from_strangers": True
                }
            }
        }

# === RESPONSE MODELS (What we send back to users) ===

class UserProfile(BaseModel):
    id: int
    username: str
    full_name: str
    bio: Optional[str] = None
    location: Optional[str] = None
    website: Optional[HttpUrl] = None
    profile_picture_url: Optional[str] = None
    followers_count: int = 0
    following_count: int = 0
    posts_count: int = 0
    verified: bool = False
    joined_date: date
    
    class Config:
        schema_extra = {
            "example": {
                "id": 12345,
                "username": "alexj_photos",
                "full_name": "Alex Johnson",
                "bio": "📸 Photography enthusiast | 🌍 Travel lover",
                "location": "San Francisco, CA",
                "followers_count": 1250,
                "following_count": 340,
                "posts_count": 89,
                "verified": False,
                "joined_date": "2023-01-15"
            }
        }

class PostResponse(BaseModel):
    id: int
    content: str
    post_type: PostType
    author: UserProfile
    created_at: datetime
    likes_count: int = 0
    comments_count: int = 0
    shares_count: int = 0
    privacy: PrivacyLevel
    tags: List[str] = []
    location: Optional[str] = None
    media_url: Optional[str] = None
    
    class Config:
        schema_extra = {
            "example": {
                "id": 98765,
                "content": "Just watched the most amazing sunset! 🌅 Nature never fails to inspire me.",
                "post_type": "image",
                "created_at": "2024-01-15T18:30:00",
                "likes_count": 42,
                "comments_count": 8,
                "shares_count": 3,
                "privacy": "public",
                "tags": ["sunset", "nature", "photography"],
                "location": "Golden Gate Bridge, SF"
            }
        }

class CommentResponse(BaseModel):
    id: int
    content: str
    author: UserProfile
    post_id: int
    parent_comment_id: Optional[int] = None
    created_at: datetime
    likes_count: int = 0
    replies_count: int = 0

class FeedResponse(BaseModel):
    posts: List[PostResponse]
    total_posts: int
    page: int
    has_more: bool
    recommended_users: List[UserProfile] = []

# Custom exception for InstaConnect
class InstaConnectError(Exception):
    def __init__(self, message: str, error_code: str):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)

@app.exception_handler(InstaConnectError)
async def instaconnect_exception_handler(request, exc: InstaConnectError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": exc.error_code,
            "message": exc.message,
            "support": "Contact support@instaconnect.com for help"
        },
    )

# === MAIN PLATFORM ROUTES ===

@app.get("/")
def platform_home():
    """🏠 Welcome to InstaConnect - Where connections come to life!"""
    return {
        "message": "📱 Welcome to InstaConnect!",
        "tagline": "Where every moment becomes a memory, and every connection counts ✨",
        "daily_stats": {
            "active_users": 125000,
            "posts_today": 45000,
            "new_connections": 8200
        },
        "trending_hashtags": ["#MondayMotivation", "#TechLife", "#Foodie", "#Travel", "#Photography"],
        "platform_features": [
            "📸 Share photos and videos",
            "💬 Connect with friends",
            "🌟 Discover new content",
            "📊 Track your engagement",
            "🔔 Real-time notifications"
        ]
    }

# === USER REGISTRATION & PROFILES ===

@app.post("/auth/signup", response_model=UserProfile, status_code=status.HTTP_201_CREATED)
def create_user_account(user_data: UserSignup):
    """
    🎉 Join the InstaConnect community!
    
    Create your account and start connecting with amazing people around the world.
    """
    # In real app, hash password and save to database
    hashed_password = hashlib.sha256(user_data.password.encode()).hexdigest()
    
    # Mock user creation
    new_user = {
        "id": 12345,
        "username": user_data.username,
        "full_name": user_data.full_name,
        "bio": user_data.bio,
        "location": None,
        "website": None,
        "profile_picture_url": f"https://api.instaconnect.com/avatars/{user_data.username}",
        "followers_count": 0,
        "following_count": 0,
        "posts_count": 0,
        "verified": False,
        "joined_date": date.today()
    }
    
    return new_user

@app.get("/users/{username}", response_model=UserProfile)
def get_user_profile(
    username: str = Path(..., min_length=3, max_length=30, description="Username to look up"),
    include_recent_posts: bool = Query(False, description="Include user's recent posts")
):
    """
    👤 Discover amazing people on InstaConnect!
    
    View profiles, see what they're up to, and connect with like-minded individuals.
    """
    # Mock user lookup
    if username not in ["alexj_photos", "travel_sarah", "techguru_mike"]:
        raise HTTPException(
            status_code=404, 
            detail=f"🔍 User @{username} not found. They might be exploring other galaxies! 🚀"
        )
    
    mock_profiles = {
        "alexj_photos": {
            "id": 12345,
            "username": "alexj_photos",
            "full_name": "Alex Johnson",
            "bio": "📸 Photography enthusiast | 🌍 Travel lover | ☕ Coffee addict",
            "location": "San Francisco, CA",
            "followers_count": 1250,
            "following_count": 340,
            "posts_count": 89,
            "verified": False,
            "joined_date": "2023-01-15"
        }
    }
    
    profile = mock_profiles.get(username, mock_profiles["alexj_photos"])
    
    return profile

@app.put("/users/me/profile", response_model=UserProfile)
def update_my_profile(updates: ProfileUpdate):
    """
    ✏️ Update your InstaConnect profile!
    
    Keep your profile fresh and let your personality shine through.
    """
    # Mock profile update
    updated_profile = {
        "id": 12345,
        "username": "current_user",
        "full_name": updates.full_name or "Current User",
        "bio": updates.bio,
        "location": updates.location,
        "website": str(updates.website) if updates.website else None,
        "profile_picture_url": "https://api.instaconnect.com/avatars/current_user",
        "followers_count": 567,
        "following_count": 234,
        "posts_count": 42,
        "verified": False,
        "joined_date": "2023-01-15"
    }
    
    return updated_profile

# === POSTS & CONTENT CREATION ===

@app.post("/posts/", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
def create_post(post: PostCreate):
    """
    📝 Share your story with the world!
    
    Create engaging posts that inspire, entertain, and connect with your community.
    """
    # Mock post creation
    mock_author = {
        "id": 12345,
        "username": "current_user",
        "full_name": "Current User",
        "bio": "Living my best life! ✨",
        "followers_count": 567,
        "following_count": 234,
        "posts_count": 43,  # Incremented after this post
        "verified": False,
        "joined_date": "2023-01-15"
    }
    
    new_post = {
        "id": 98765,
        "content": post.content,
        "post_type": post.post_type,
        "author": mock_author,
        "created_at": datetime.now(),
        "likes_count": 0,
        "comments_count": 0,
        "shares_count": 0,
        "privacy": post.privacy,
        "tags": post.tags,
        "location": post.location,
        "media_url": str(post.media_url) if post.media_url else None
    }
    
    return new_post

@app.get("/posts/{post_id}", response_model=PostResponse)
def get_post_details(
    post_id: int = Path(..., ge=1, description="The post ID you want to view"),
    include_comments: bool = Query(False, description="Include comments in response")
):
    """
    📖 Dive into amazing content!
    
    Explore posts, read comments, and engage with the community.
    """
    if post_id not in [98765, 98766, 98767]:
        raise InstaConnectError(
            message=f"Post #{post_id} seems to have vanished into the digital void! 🌌",
            error_code="POST_NOT_FOUND"
        )
    
    # Mock post data
    mock_author = {
        "id": 12345,
        "username": "alexj_photos",
        "full_name": "Alex Johnson",
        "bio": "📸 Photography enthusiast",
        "followers_count": 1250,
        "following_count": 340,
        "posts_count": 89,
        "verified": False,
        "joined_date": "2023-01-15"
    }
    
    return {
        "id": post_id,
        "content": "Just watched the most amazing sunset! 🌅 Nature never fails to inspire me.",
        "post_type": "image",
        "author": mock_author,
        "created_at": datetime.now(),
        "likes_count": 42,
        "comments_count": 8,
        "shares_count": 3,
        "privacy": "public",
        "tags": ["sunset", "nature", "photography"],
        "location": "Golden Gate Bridge, SF",
        "media_url": "https://images.instaconnect.com/sunset_golden_gate.jpg"
    }

# === SOCIAL INTERACTIONS ===

@app.post("/posts/{post_id}/comments/", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
def add_comment(
    post_id: int = Path(..., ge=1),
    comment: CommentCreate = Body(...)
):
    """
    💬 Join the conversation!
    
    Share your thoughts, ask questions, and connect through meaningful discussions.
    """
    # Mock comment creation
    mock_author = {
        "id": 12345,
        "username": "current_user",
        "full_name": "Current User",
        "followers_count": 567,
        "posts_count": 42,
        "verified": False,
        "joined_date": "2023-01-15"
    }
    
    new_comment = {
        "id": 54321,
        "content": comment.content,
        "author": mock_author,
        "post_id": post_id,
        "parent_comment_id": comment.parent_comment_id,
        "created_at": datetime.now(),
        "likes_count": 0,
        "replies_count": 0
    }
    
    return new_comment

@app.post("/posts/{post_id}/react/")
def react_to_post(
    post_id: int = Path(..., ge=1),
    reaction: ReactionType = Body(..., description="Your reaction to this post")
):
    """
    ❤️ Express yourself!
    
    Show your appreciation with reactions that speak louder than words.
    """
    reaction_messages = {
        ReactionType.LIKE: "👍 You liked this post!",
        ReactionType.LOVE: "❤️ You love this post!",
        ReactionType.LAUGH: "😂 This made you laugh!",
        ReactionType.WOW: "😮 This amazed you!",
        ReactionType.ANGRY: "😠 This made you angry!",
        ReactionType.CARE: "🤗 You care about this!"
    }
    
    return {
        "post_id": post_id,
        "reaction": reaction,
        "message": reaction_messages[reaction],
        "total_reactions": 43,  # Mock count
        "your_reaction": reaction.value
    }

# === FEED & DISCOVERY ===

@app.get("/feed/", response_model=FeedResponse)
def get_personalized_feed(
    page: int = Query(1, ge=1, description="Page number for pagination"),
    limit: int = Query(10, ge=1, le=50, description="Number of posts per page"),
    feed_type: str = Query("home", description="Feed type: home, trending, or following")
):
    """
    🌟 Discover amazing content!
    
    Your personalized feed with posts from friends, trending content, and recommendations.
    """
    # Mock feed data
    mock_posts = []
    for i in range(limit):
        post_id = 98765 + i
        mock_posts.append({
            "id": post_id,
            "content": f"Amazing post #{i+1} - Living the dream! ✨",
            "post_type": "text" if i % 2 == 0 else "image",
            "author": {
                "id": 12345 + i,
                "username": f"user_{i+1}",
                "full_name": f"Amazing User {i+1}",
                "followers_count": 100 + i * 50,
                "verified": i % 5 == 0,
                "joined_date": "2023-01-15"
            },
            "created_at": datetime.now(),
            "likes_count": 10 + i * 5,
            "comments_count": 2 + i,
            "shares_count": i,
            "privacy": "public",
            "tags": ["lifestyle", "inspiration"],
            "location": f"City #{i+1}"
        })
    
    recommended_users = [
        {
            "id": 99999,
            "username": "photography_pro",
            "full_name": "Pro Photographer",
            "bio": "📸 Professional photographer | 🌍 World traveler",
            "followers_count": 25000,
            "verified": True,
            "joined_date": "2022-05-10"
        }
    ]
    
    return {
        "posts": mock_posts,
        "total_posts": 1000,  # Mock total
        "page": page,
        "has_more": page < 10,  # Mock pagination
        "recommended_users": recommended_users
    }

# === FILE UPLOADS ===

@app.post("/media/upload/")
def upload_media(
    file: UploadFile = File(..., description="Image or video file to upload"),
    caption: Optional[str] = Form(None, description="Optional caption for your media"),
    tags: str = Form("", description="Comma-separated tags")
):
    """
    📸 Upload and share your memories!
    
    Share photos and videos that capture your most precious moments.
    """
    # Validate file type
    allowed_types = {
        "image/jpeg", "image/png", "image/gif", "image/webp",
        "video/mp4", "video/mpeg", "video/quicktime"
    }
    
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail="📷 Only images (JPEG, PNG, GIF, WebP) and videos (MP4, MPEG, MOV) are allowed!"
        )
    
    # Mock file processing
    file_id = str(uuid.uuid4())
    file_url = f"https://media.instaconnect.com/{file_id}.{file.filename.split('.')[-1]}"
    
    # Parse tags
    tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()] if tags else []
    
    return {
        "message": "📸 Media uploaded successfully!",
        "file_id": file_id,
        "file_url": file_url,
        "file_name": file.filename,
        "file_size": f"{len(file.file.read()) / 1024:.2f} KB",  # Mock size
        "content_type": file.content_type,
        "caption": caption,
        "tags": tag_list,
        "upload_time": datetime.now().isoformat(),
        "processing_status": "✅ Ready to share!"
    }

# === FORM DATA EXAMPLES ===

@app.post("/auth/login/")
def login_user(
    username: str = Form(..., description="Your username or email"),
    password: str = Form(..., description="Your password"),
    remember_me: bool = Form(False, description="Stay logged in")
):
    """
    🔐 Welcome back to InstaConnect!
    
    Sign in to your account and reconnect with your community.
    """
    # Mock authentication
    if username == "demo" and password == "password123":
        return {
            "message": "🎉 Welcome back!",
            "access_token": "mock_jwt_token_here",
            "user": {
                "username": username,
                "full_name": "Demo User",
                "profile_picture": f"https://api.instaconnect.com/avatars/{username}"
            },
            "remember_me": remember_me,
            "expires_in": "7 days" if remember_me else "24 hours"
        }
    else:
        raise HTTPException(
            status_code=401,
            detail="🔐 Invalid credentials. Please check your username and password!"
        )

# === DIFFERENT RESPONSE TYPES ===

@app.get("/share/{post_id}", response_class=HTMLResponse)
def share_post_page(post_id: int):
    """
    🔗 Share posts with beautiful preview pages!
    
    Generate shareable HTML pages for social media and messaging apps.
    """
    return f"""
    <!DOCTYPE html>
    <html>
        <head>
            <title>Amazing Post on InstaConnect</title>
            <meta property="og:title" content="Check out this amazing post!">
            <meta property="og:description" content="Join InstaConnect to see more content like this">
            <meta property="og:image" content="https://images.instaconnect.com/post_{post_id}_preview.jpg">
            <meta property="og:url" content="https://instaconnect.com/posts/{post_id}">
            <style>
                body {{ font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; }}
                .post {{ border: 1px solid #ddd; border-radius: 8px; padding: 20px; }}
                .author {{ display: flex; align-items: center; margin-bottom: 15px; }}
                .avatar {{ width: 40px; height: 40px; border-radius: 50%; margin-right: 10px; background: #4f46e5; }}
                .content {{ font-size: 18px; line-height: 1.6; }}
                .cta {{ background: #4f46e5; color: white; padding: 15px 30px; border: none; border-radius: 8px; font-size: 16px; margin-top: 20px; }}
            </style>
        </head>
        <body>
            <div class="post">
                <div class="author">
                    <div class="avatar"></div>
                    <strong>Amazing User</strong>
                </div>
                <div class="content">
                    "Just had the most incredible experience! 🌟 Life is full of surprises and I'm grateful for every moment."
                </div>
                <button class="cta" onclick="window.open('https://instaconnect.com/signup', '_blank')">
                    Join InstaConnect to See More! 📱
                </button>
            </div>
        </body>
    </html>
    """

@app.get("/analytics/engagement/{post_id}")
def get_engagement_analytics(
    post_id: int,
    format: str = Query("json", description="Response format: json or csv")
):
    """
    📊 Track your post performance!
    
    Get detailed analytics about how your content is performing.
    """
    analytics_data = {
        "post_id": post_id,
        "total_views": 15420,
        "unique_viewers": 12890,
        "likes": 342,
        "comments": 89,
        "shares": 67,
        "saves": 156,
        "engagement_rate": 4.2,
        "best_performing_time": "6:00 PM - 8:00 PM",
        "top_demographics": {
            "age_group": "25-34",
            "location": "San Francisco Bay Area",
            "interests": ["photography", "travel", "lifestyle"]
        }
    }
    
    if format == "csv":
        # Return CSV format
        csv_content = "metric,value\n"
        csv_content += f"total_views,{analytics_data['total_views']}\n"
        csv_content += f"unique_viewers,{analytics_data['unique_viewers']}\n"
        csv_content += f"likes,{analytics_data['likes']}\n"
        csv_content += f"comments,{analytics_data['comments']}\n"
        csv_content += f"engagement_rate,{analytics_data['engagement_rate']}%\n"
        
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=post_{post_id}_analytics.csv"}
        )
    
    return analytics_data

# === PRACTICE EXERCISE SOLUTION: STORIES FEATURE ===

class StoryCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=500, description="Your story content")
    media_url: Optional[HttpUrl] = Field(None, description="Image or video for your story")
    background_color: Optional[str] = Field("#ffffff", description="Background color for text stories")
    expires_in_hours: int = Field(24, ge=1, le=72, description="Story expiration (1-72 hours)")
    
    @validator('background_color')
    def validate_color(cls, v):
        if not v.startswith('#') or len(v) != 7:
            raise ValueError('Background color must be a valid hex color (e.g., #ffffff)')
        return v

class StoryResponse(BaseModel):
    id: int
    content: str
    author: UserProfile
    media_url: Optional[str] = None
    background_color: str
    created_at: datetime
    expires_at: datetime
    views_count: int = 0
    is_expired: bool = False

@app.post("/stories/", response_model=StoryResponse, status_code=status.HTTP_201_CREATED)
def create_story(story: StoryCreate):
    """
    📸 Share your moment with Stories!
    
    Create ephemeral content that disappears after 24 hours - perfect for sharing
    spontaneous moments and behind-the-scenes content.
    """
    from datetime import timedelta
    
    mock_author = {
        "id": 12345,
        "username": "current_user",
        "full_name": "Current User",
        "bio": "Living in the moment! ✨",
        "followers_count": 567,
        "posts_count": 42,
        "verified": False,
        "joined_date": "2023-01-15"
    }
    
    now = datetime.now()
    expires_at = now + timedelta(hours=story.expires_in_hours)
    
    new_story = {
        "id": 77777,
        "content": story.content,
        "author": mock_author,
        "media_url": str(story.media_url) if story.media_url else None,
        "background_color": story.background_color,
        "created_at": now,
        "expires_at": expires_at,
        "views_count": 0,
        "is_expired": False
    }
    
    return new_story

@app.get("/stories/", response_model=List[StoryResponse])
def get_stories_feed(
    include_expired: bool = Query(False, description="Include expired stories"),
    limit: int = Query(20, ge=1, le=100, description="Maximum stories to return")
):
    """
    👀 Catch up on the latest Stories!
    
    See what your friends are up to with Stories from the past 24 hours.
    """
    # Mock stories data
    from datetime import timedelta
    
    mock_stories = []
    for i in range(min(limit, 10)):  # Mock 10 stories
        story_time = datetime.now() - timedelta(hours=i*2)
        is_expired = (datetime.now() - story_time).total_seconds() > 24*3600
        
        if is_expired and not include_expired:
            continue
            
        mock_stories.append({
            "id": 77777 + i,
            "content": f"Amazing moment #{i+1}! 🌟",
            "author": {
                "id": 12345 + i,
                "username": f"storyteller_{i+1}",
                "full_name": f"Story User {i+1}",
                "followers_count": 100 + i * 20,
                "verified": i % 3 == 0,
                "joined_date": "2023-01-15"
            },
            "media_url": f"https://stories.instaconnect.com/story_{77777+i}.jpg" if i % 2 == 0 else None,
            "background_color": "#4f46e5" if i % 2 == 1 else "#ffffff",
            "created_at": story_time,
            "expires_at": story_time + timedelta(hours=24),
            "views_count": 50 + i * 10,
            "is_expired": is_expired
        })
    
    return mock_stories

if __name__ == "__main__":
    import uvicorn
    print("📱 Starting InstaConnect Social Media Platform...")
    print("✨ Where connections come to life!")
    uvicorn.run(app, host="0.0.0.0", port=8000) 