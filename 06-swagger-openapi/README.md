# 📚 Section 6: OpenAPI & Swagger Documentation - AI Assistant Marketplace

Master **API documentation** by building an AI assistant marketplace! Learn how to create beautiful, interactive documentation that makes developers love your API through FastAPI's automatic OpenAPI generation.

## 🎯 What You'll Learn

- Automatic OpenAPI specification generation
- Custom documentation with rich descriptions
- Interactive testing with Swagger UI
- API organization with tags and metadata
- Professional branding and examples

## 🤖 Meet AI Assistant Marketplace

Our AI platform demonstrates documentation excellence through:

**Key Features:**
- 🤖 Custom AI assistant creation and management
- 💬 Real-time conversation interfaces
- 🏪 Marketplace for sharing AI assistants
- 👤 User profiles and subscription management
- 📊 Analytics and usage tracking

## 🚀 Core Documentation Concepts

### **1. FastAPI Documentation Magic**

```python
from fastapi import FastAPI, Query, Path, Body
from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum

app = FastAPI(
    title="🤖 AI Assistant Marketplace",
    description="""
    Welcome to the **AI Assistant Marketplace** - where cutting-edge AI meets human creativity! 🚀
    
    ## 🌟 What You Can Do Here
    * 🎨 **Creative Assistants**: Art, writing, music composition
    * 🧠 **Analytical Assistants**: Data analysis, research, problem-solving  
    * 💼 **Business Assistants**: Meeting scheduling, email management
    * 🎓 **Educational Assistants**: Tutoring, language learning
    
    *Built with ❤️ using FastAPI - Making AI accessible to everyone!*
    """,
    version="3.0.0",
    contact={
        "name": "AI Marketplace Support Team",
        "url": "https://aimarketplace.com/support",
        "email": "support@aimarketplace.com",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    }
)
```

**FastAPI automatically creates:**
- ✨ Interactive Swagger UI at `/docs`
- 📖 Clean ReDoc interface at `/redoc`  
- 🔧 OpenAPI JSON schema at `/openapi.json`

### **2. Rich Model Documentation**

```python
class AISpecialty(str, Enum):
    """AI Assistant specialization areas"""
    CREATIVE = "creative"
    ANALYTICAL = "analytical"
    BUSINESS = "business"
    EDUCATIONAL = "educational"

class AIAssistantCreate(BaseModel):
    """Create a new AI assistant with specific capabilities"""
    
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
        description="Detailed description of capabilities",
        example="AI assistant specialized in creative writing and storytelling."
    )
    specialty: AISpecialty = Field(
        ...,
        description="Primary specialization area",
        example=AISpecialty.CREATIVE
    )
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Python Coding Mentor",
                "description": "Expert Python developer assistant for code review",
                "specialty": "technical"
            }
        }
```

### **3. Comprehensive Endpoint Documentation**

```python
@app.post(
    "/assistants/",
    response_model=AIAssistantResponse,
    status_code=201,
    tags=["🤖 AI Assistants"],
    summary="Create a new AI assistant",
    description="Design and deploy your own custom AI assistant",
    response_description="Newly created assistant details",
    responses={
        201: {"description": "Assistant created successfully"},
        400: {"description": "Invalid assistant configuration"},
        402: {"description": "Insufficient credits to create assistant"}
    }
)
def create_ai_assistant(assistant_data: AIAssistantCreate):
    """
    🎨 **Create Your Own AI Assistant!**
    
    Bring your vision to life by creating a custom AI assistant.
    
    ### 🛠️ What You Can Customize:
    - **Personality**: Define communication style
    - **Expertise**: Choose specialization areas  
    - **Behavior**: Set response tone and approach
    
    ### 💡 Creation Tips:
    - Be specific about the assistant's role
    - Define clear personality traits
    - Use relevant tags for discoverability
    """
    return create_new_assistant(assistant_data)
```

## 🎯 Advanced Documentation Features

### **1. Organizing with Tags**

```python
app = FastAPI(
    openapi_tags=[
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
        }
    ]
)
```

### **2. Custom Response Examples**

```python
class ConversationResponse(BaseModel):
    id: str
    assistant_id: str
    messages: List[MessageResponse]
    created_at: datetime
    
    class Config:
        schema_extra = {
            "examples": {
                "creative_writing": {
                    "summary": "Creative Writing Session",
                    "value": {
                        "id": "conv_123",
                        "assistant_id": "assistant_456",
                        "messages": [
                            {
                                "role": "user",
                                "content": "Help me write a poem about AI"
                            },
                            {
                                "role": "assistant", 
                                "content": "Here's a poem about AI and human creativity..."
                            }
                        ]
                    }
                },
                "business_meeting": {
                    "summary": "Business Meeting Planning",
                    "value": {
                        "id": "conv_789",
                        "assistant_id": "assistant_101",
                        "messages": [
                            {
                                "role": "user",
                                "content": "Schedule a team meeting for next week"
                            }
                        ]
                    }
                }
            }
        }
```

### **3. Error Response Documentation**

```python
from fastapi import HTTPException

@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={
            "error": "RESOURCE_NOT_FOUND",
            "message": "The requested AI assistant was not found",
            "suggestion": "Check the assistant ID or browse available assistants"
        }
    )

@app.get(
    "/assistants/{assistant_id}",
    response_model=AIAssistantResponse,
    tags=["🤖 AI Assistants"],
    responses={
        200: {"description": "Assistant details retrieved successfully"},
        404: {
            "description": "Assistant not found",
            "content": {
                "application/json": {
                    "example": {
                        "error": "RESOURCE_NOT_FOUND",
                        "message": "Assistant not found",
                        "suggestion": "Check the assistant ID"
                    }
                }
            }
        }
    }
)
def get_assistant(assistant_id: str = Path(..., description="Unique assistant identifier")):
    """Get detailed information about a specific AI assistant"""
    return get_assistant_by_id(assistant_id)
```

## 🔒 Security Documentation

### **Authentication Schemes**

```python
from fastapi.security import HTTPBearer, OAuth2PasswordBearer

security = HTTPBearer()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

@app.post(
    "/auth/login",
    tags=["🔐 Authentication"],
    summary="Login to get access token",
    description="Authenticate with email/password to receive JWT token"
)
def login(credentials: UserCredentials):
    """
    🔐 **Authenticate and Get Access Token**
    
    Login with your credentials to receive a JWT token for API access.
    
    ### 🎫 Token Usage:
    - Include token in Authorization header: `Bearer your_token_here`
    - Tokens expire after 24 hours
    - Refresh tokens available for long-term access
    """
    return {"access_token": generate_jwt_token(credentials)}

@app.get(
    "/assistants/my-assistants",
    dependencies=[Depends(security)],
    tags=["🤖 AI Assistants"],
    summary="Get my AI assistants",
    description="Retrieve all AI assistants created by authenticated user"
)
def get_my_assistants():
    """Get your personal AI assistants (requires authentication)"""
    return get_user_assistants()
```

## 🎮 Key API Endpoints Documentation

### **Assistant Management**
```python
@app.get("/assistants/", tags=["🤖 AI Assistants"])
def browse_assistants(
    specialty: Optional[AISpecialty] = None,
    search: Optional[str] = Query(None, description="Search assistants by name")
):
    """Browse and discover AI assistants"""

@app.put("/assistants/{assistant_id}", tags=["🤖 AI Assistants"])
def update_assistant(assistant_id: str, updates: AIAssistantUpdate):
    """Update an existing AI assistant"""
```

### **Conversation Management**
```python
@app.post("/conversations/", tags=["💬 Conversations"])
def start_conversation(assistant_id: str, initial_message: str):
    """Start a new conversation with an AI assistant"""

@app.post("/conversations/{conversation_id}/messages", tags=["💬 Conversations"])
def send_message(conversation_id: str, message: MessageCreate):
    """Send a message in an existing conversation"""
```

## 🛠️ Running Documentation

```bash
cd 06-swagger-openapi
uvicorn main:app --reload

# Access documentation:
# Swagger UI: http://localhost:8000/docs
# ReDoc: http://localhost:8000/redoc
# OpenAPI JSON: http://localhost:8000/openapi.json
```

## 📊 Documentation Best Practices

| Practice | Description | Example |
|----------|-------------|---------|
| **Rich Descriptions** | Clear, helpful field descriptions | `Field(description="User's email address")` |
| **Examples** | Real-world data examples | `example="user@example.com"` |
| **Response Codes** | Document all possible responses | `responses={404: {"description": "Not found"}}` |
| **Tags** | Organize endpoints logically | `tags=["🤖 AI Assistants"]` |
| **Docstrings** | Detailed endpoint documentation | Multi-line function docstrings |

## 🎮 Practice Exercises

1. **📊 Analytics Endpoints**: Document usage statistics and metrics
2. **🔐 Authentication Flow**: Document OAuth2 and API key authentication
3. **📁 File Upload**: Document assistant avatar and training data uploads
4. **🔔 Webhooks**: Document real-time notification endpoints

## 💡 Documentation Benefits

### **For Developers**
- **Self-Service**: Find answers without support tickets
- **Interactive Testing**: Try endpoints directly in browser
- **Code Generation**: Generate client SDKs automatically
- **Quick Integration**: Copy-paste working examples

### **For Your API**
- **Higher Adoption**: Clear docs increase usage
- **Fewer Support Requests**: Self-documenting reduces tickets
- **Professional Image**: Good docs show quality
- **Better Feedback**: Easy testing leads to better feedback

## 🚀 What's Next?

In **Section 7: Async Programming**, we'll build a real-time gaming platform that shows how to handle thousands of concurrent users with asynchronous FastAPI!

**Key Takeaway**: Great documentation is your API's best marketing tool - it turns confused visitors into happy, productive users! 📚✨ 