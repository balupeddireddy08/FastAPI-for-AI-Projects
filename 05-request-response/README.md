# 📱 Section 5: Request & Response Models - InstaConnect Social Media

Master **request and response modeling** by building a social media platform! Learn how to validate user input, structure API responses, handle file uploads, and ensure data security through proper model design.

## 🎯 What You'll Learn

- Request models with Pydantic validation
- Response models for structured data output
- Custom validators for complex business rules
- File upload handling and form data
- Security best practices with data filtering

## 📱 Meet InstaConnect Social Media

Our social platform demonstrates advanced data modeling through:

**Key Features:**
- 👤 User registration with validation
- 📝 Post creation with content filtering
- 💬 Comment system with nested responses
- 📁 Media upload with progress tracking
- 🔒 Security-first data handling

## 🚀 Core Request/Response Concepts

### **1. Request Models - Data Coming In**

```python
from pydantic import BaseModel, Field, EmailStr, validator
from enum import Enum
from typing import List, Optional

class PostType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    STORY = "story"

class UserSignup(BaseModel):
    username: str = Field(..., min_length=3, max_length=30)
    email: EmailStr = Field(..., description="Your email address")
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=1, max_length=100)
    date_of_birth: date = Field(..., description="Your birthday")
    
    @validator('username')
    def username_alphanumeric(cls, v):
        if not v.replace('_', '').isalnum():
            raise ValueError('Username can only contain letters, numbers, and underscores')
        return v.lower()
    
    @validator('password')
    def password_strength(cls, v):
        checks = [
            (any(c.isdigit() for c in v), "at least one number"),
            (any(c.isupper() for c in v), "at least one uppercase letter"),
            (any(c in "!@#$%^&*()_+-=" for c in v), "at least one special character")
        ]
        failed_checks = [msg for passed, msg in checks if not passed]
        if failed_checks:
            raise ValueError(f"Password must contain {', '.join(failed_checks)}")
        return v
```

### **2. Response Models - Data Going Out**

```python
class UserProfile(BaseModel):
    id: int
    username: str
    full_name: str
    bio: Optional[str] = None
    followers_count: int = 0
    following_count: int = 0
    posts_count: int = 0
    verified: bool = False
    joined_date: date
    # Notice: NO PASSWORD in response model! 🔒

class PostResponse(BaseModel):
    id: int
    content: str
    post_type: PostType
    author: UserProfile  # Nested model
    created_at: datetime
    likes_count: int = 0
    comments_count: int = 0
    tags: List[str] = []
    location: Optional[str] = None
    
    class Config:
        schema_extra = {
            "example": {
                "id": 98765,
                "content": "Just watched an amazing sunset! 🌅",
                "post_type": "image",
                "likes_count": 42,
                "tags": ["sunset", "nature"]
            }
        }
```

## 🎯 Advanced Validation Patterns

### **1. Post Creation with Custom Validation**

```python
class PostCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=2200)
    post_type: PostType = Field(PostType.TEXT)
    tags: List[str] = Field([], description="Tag friends or topics")
    location: Optional[str] = Field(None, max_length=100)
    
    @validator('content')
    def content_not_empty_after_strip(cls, v):
        if not v.strip():
            raise ValueError('Post content cannot be empty')
        return v.strip()
    
    @validator('tags')
    def validate_tags(cls, v):
        if len(v) > 10:
            raise ValueError('Maximum 10 tags allowed per post')
        return [tag.lower().strip() for tag in v]

@app.post("/posts/", response_model=PostResponse, status_code=201)
def create_post(post: PostCreate):
    return save_post_to_database(post)
```

### **2. Form Data and File Uploads**

```python
from fastapi import Form, File, UploadFile

@app.post("/media/upload/")
def upload_media(
    file: UploadFile = File(..., description="Image or video file"),
    caption: Optional[str] = Form(None, description="Optional caption"),
    tags: str = Form("", description="Comma-separated tags")
):
    # Validate file type
    if not file.content_type.startswith(('image/', 'video/')):
        raise HTTPException(status_code=400, detail="Only images and videos allowed")
    
    # Process tags
    tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
    
    return {
        "filename": file.filename,
        "content_type": file.content_type,
        "size": file.size,
        "caption": caption,
        "tags": tag_list
    }
```

### **3. Login with Form Data**

```python
from fastapi.security import OAuth2PasswordRequestForm

@app.post("/auth/login/")
def login_user(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    remember_me: bool = Form(False)
):
    # Authenticate user
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    return {
        "access_token": create_access_token(user.id),
        "token_type": "bearer",
        "expires_in": 3600 if not remember_me else 86400
    }
```

## 🔒 Security Best Practices

### **1. Response Model Filtering**

```python
# Input model (includes password)
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

# Output model (excludes password)
class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    # No password field - automatically filtered out!

@app.post("/users/", response_model=UserResponse)
def create_user(user: UserCreate):
    # Password is processed but never returned
    return create_new_user(user)
```

### **2. Custom Exception Handling**

```python
class InstaConnectError(Exception):
    def __init__(self, message: str, error_code: str):
        self.message = message
        self.error_code = error_code

@app.exception_handler(InstaConnectError)
async def handle_custom_error(request, exc: InstaConnectError):
    return JSONResponse(
        status_code=400,
        content={
            "error": exc.error_code,
            "message": exc.message,
            "timestamp": datetime.now().isoformat()
        }
    )
```

## 🎮 Key API Endpoints

### **User Management**
```python
@app.post("/auth/signup", response_model=UserProfile, status_code=201)
def create_user_account(user_data: UserSignup)

@app.get("/users/{username}", response_model=UserProfile)
def get_user_profile(username: str)

@app.put("/users/me/profile", response_model=UserProfile)  
def update_my_profile(updates: ProfileUpdate)
```

### **Content Creation**
```python
@app.post("/posts/", response_model=PostResponse, status_code=201)
def create_post(post: PostCreate)

@app.post("/posts/{post_id}/comments/", response_model=CommentResponse)
def add_comment(post_id: int, comment: CommentCreate)

@app.post("/posts/{post_id}/react/")
def react_to_post(post_id: int, reaction: ReactionType)
```

### **Feed & Discovery**
```python
@app.get("/feed/", response_model=FeedResponse)
def get_personalized_feed(page: int = 1, limit: int = 10)

@app.get("/posts/{post_id}", response_model=PostResponse)
def get_post_details(post_id: int, include_comments: bool = False)
```

## 🛠️ Running InstaConnect

```bash
cd 05-request-response
uvicorn main:app --reload

# Try these endpoints:
# POST /auth/signup (create account)
# POST /auth/login (get access token)
# POST /posts/ (create post)
# POST /media/upload/ (upload files)
```

## 📊 Request vs Response Models

| Model Type | Purpose | Security | Validation |
|------------|---------|----------|------------|
| **Request** | Data coming in | Validate all input | Strong validation rules |
| **Response** | Data going out | Filter sensitive fields | Format for presentation |

## 🎮 Practice Exercises

1. **🔐 Password Reset**: Create models for password reset workflow
2. **📁 Media Management**: Add image metadata and processing
3. **👥 Friend Requests**: Build friendship management system
4. **📊 Analytics**: Add post engagement tracking models

## 💡 Best Practices

### **Validation Rules**
- Always validate user input
- Use meaningful error messages
- Implement custom validators for business logic
- Check data relationships and constraints

### **Security Guidelines**
- Never return passwords in responses
- Filter sensitive data at the model level
- Validate file uploads thoroughly
- Sanitize content to prevent XSS

### **Model Design**
- Keep models focused and single-purpose
- Use nested models for complex data
- Add examples to improve documentation
- Design for both usability and security

## 🚀 What's Next?

In **Section 6: Documentation**, we'll build an AI assistant marketplace that shows how to create beautiful, interactive API documentation that makes developers love your platform!

**Key Takeaway**: Great APIs have great data models - they validate input thoroughly and return data safely and consistently! 📱✨ 