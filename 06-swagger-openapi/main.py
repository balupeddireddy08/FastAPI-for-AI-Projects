from fastapi import FastAPI, Path, Query, Body, Depends, Security, HTTPException, status, Header
from fastapi.openapi.utils import get_openapi
from fastapi.security import APIKeyHeader, OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict
from enum import Enum
import uuid

# Initialize FastAPI with custom metadata
app = FastAPI(
    title="AI Project API",
    description="""
    # AI Project API Documentation
    
    This API allows you to interact with various AI models and tools.
    
    ## Features
    
    * **Model Management**: Create, update, and delete AI models
    * **Prediction**: Get predictions from AI models
    * **Training**: Train models on new data
    * **Monitoring**: Monitor model performance
    
    ## Getting Started
    
    To get started, you'll need an API key. Contact the administrator to get one.
    """,
    version="1.0.0",
    terms_of_service="https://example.com/terms/",
    contact={
        "name": "API Support",
        "url": "https://example.com/support",
        "email": "support@example.com",
    },
    license_info={
        "name": "Apache 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
    },
    openapi_tags=[
        {
            "name": "models",
            "description": "Operations with AI models",
            "externalDocs": {
                "description": "Models Documentation",
                "url": "https://example.com/docs/models",
            },
        },
        {
            "name": "predictions",
            "description": "Get predictions from AI models",
        },
        {
            "name": "users",
            "description": "User management operations",
        },
        {
            "name": "admin",
            "description": "Administrative operations",
        },
    ],
)

# Define enums for better documentation
class ModelType(str, Enum):
    classification = "classification"
    regression = "regression"
    clustering = "clustering"
    nlp = "nlp"
    computer_vision = "computer_vision"

class ModelFramework(str, Enum):
    tensorflow = "tensorflow"
    pytorch = "pytorch"
    sklearn = "sklearn"
    xgboost = "xgboost"
    custom = "custom"

# Define models with examples and documentation
class ModelBase(BaseModel):
    name: str = Field(
        ..., 
        title="Model Name",
        description="The name of the AI model",
        min_length=1, 
        max_length=100,
        example="sentiment_analyzer"
    )
    description: Optional[str] = Field(
        None, 
        title="Model Description",
        description="A detailed description of what the model does",
        max_length=1000,
        example="Sentiment analysis model trained on tweets"
    )
    model_type: ModelType = Field(
        ...,
        title="Model Type",
        description="The type of machine learning task this model performs"
    )
    framework: ModelFramework = Field(
        ...,
        title="Framework",
        description="The framework or library used for this model"
    )
    version: str = Field(
        "1.0.0", 
        title="Model Version",
        description="The semantic version of the model",
        example="1.0.0"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "name": "image_classifier",
                "description": "A model that classifies images into categories",
                "model_type": "computer_vision",
                "framework": "pytorch",
                "version": "2.1.0"
            }
        }

class ModelCreate(ModelBase):
    training_data: str = Field(
        ...,
        title="Training Data Path",
        description="Path to the training data for this model",
        example="/data/training/images/"
    )
    parameters: Dict[str, any] = Field(
        {},
        title="Model Parameters",
        description="Parameters for model training and inference",
        example={"learning_rate": 0.001, "batch_size": 32}
    )

class ModelInDB(ModelBase):
    id: str = Field(
        ...,
        title="Model ID",
        description="Unique identifier for the model"
    )
    created_at: str = Field(
        ...,
        title="Creation Time",
        description="When the model was created",
        example="2023-01-15T00:00:00Z"
    )
    owner_id: str = Field(
        ...,
        title="Owner ID",
        description="ID of the user who owns this model"
    )

class UserCreate(BaseModel):
    username: str = Field(
        ..., 
        title="Username",
        description="Unique username for the user",
        min_length=3,
        max_length=50,
        example="johndoe"
    )
    email: EmailStr = Field(
        ...,
        title="Email Address",
        description="User's email address",
        example="john@example.com"
    )
    password: str = Field(
        ...,
        title="Password",
        description="User's password (will be hashed)",
        min_length=8,
        example="securepassword123"
    )
    full_name: Optional[str] = Field(
        None,
        title="Full Name",
        description="User's full name",
        example="John Doe"
    )

class UserResponse(BaseModel):
    id: str = Field(
        ...,
        title="User ID",
        description="Unique identifier for the user"
    )
    username: str = Field(
        ...,
        title="Username",
        description="User's unique username"
    )
    email: EmailStr = Field(
        ...,
        title="Email",
        description="User's email address"
    )
    full_name: Optional[str] = Field(
        None,
        title="Full Name",
        description="User's full name"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "username": "johndoe",
                "email": "john@example.com",
                "full_name": "John Doe"
            }
        }

class PredictionRequest(BaseModel):
    model_id: str = Field(
        ...,
        title="Model ID",
        description="ID of the model to use for prediction",
        example="123e4567-e89b-12d3-a456-426614174000"
    )
    data: Dict[str, any] = Field(
        ...,
        title="Input Data",
        description="The data to make predictions on",
        example={"text": "I really enjoyed this movie!"}
    )

class PredictionResponse(BaseModel):
    model_id: str = Field(
        ...,
        title="Model ID",
        description="ID of the model used for prediction"
    )
    prediction: any = Field(
        ...,
        title="Prediction",
        description="The model's prediction result"
    )
    confidence: Optional[float] = Field(
        None,
        title="Confidence",
        description="Confidence score of the prediction (0-1)",
        ge=0,
        le=1
    )
    execution_time: float = Field(
        ...,
        title="Execution Time",
        description="Time taken to make the prediction in seconds"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "model_id": "123e4567-e89b-12d3-a456-426614174000",
                "prediction": {"sentiment": "positive", "class": 1},
                "confidence": 0.92,
                "execution_time": 0.023
            }
        }

# Set up security
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_api_key(api_key: str = Security(api_key_header)):
    if api_key != "test_api_key":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API Key"
        )
    return api_key

# Define routes with detailed documentation
@app.get(
    "/",
    summary="API Welcome",
    description="Welcome endpoint with API information",
    tags=["general"]
)
def read_root():
    """
    # Welcome to the AI Project API
    
    This endpoint provides basic information about the API.
    
    ## Returns
    - `message`: Welcome message
    - `version`: API version
    - `docs_url`: URL to the API documentation
    """
    return {
        "message": "Welcome to the AI Project API",
        "version": "1.0.0",
        "docs_url": "/docs"
    }

@app.post(
    "/token",
    summary="Get access token",
    description="OAuth2 compatible token login, get an access token for future requests",
    tags=["users"]
)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    ## OAuth2 Token Generator
    
    Get an access token by providing username and password.
    
    ### Form Parameters
    - `username`: Your username
    - `password`: Your password
    
    ### Returns
    - `access_token`: Token to be used in future requests
    - `token_type`: Type of token (bearer)
    """
    # In a real app, verify credentials against database
    if form_data.username != "testuser" or form_data.password != "testpassword":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {"access_token": "fake_token", "token_type": "bearer"}

@app.get(
    "/models/",
    summary="Get all models",
    description="Get a list of all available AI models",
    response_model=List[ModelInDB],
    tags=["models"]
)
def get_models(
    skip: int = Query(0, title="Skip", description="Number of models to skip", ge=0),
    limit: int = Query(100, title="Limit", description="Maximum number of models to return", ge=1, le=1000),
    model_type: Optional[ModelType] = Query(None, title="Model Type", description="Filter by model type"),
    token: str = Depends(oauth2_scheme)
):
    """
    Retrieve all AI models with pagination and filtering.
    
    You can filter by model type and paginate results using skip and limit parameters.
    
    This endpoint requires authentication.
    """
    # In a real app, query models from database
    models = [
        {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "name": "sentiment_analyzer",
            "description": "A model for sentiment analysis of text",
            "model_type": "nlp",
            "framework": "pytorch",
            "version": "1.0.0",
            "created_at": "2023-01-15T00:00:00Z",
            "owner_id": "user123"
        },
        {
            "id": "223e4567-e89b-12d3-a456-426614174000",
            "name": "object_detector",
            "description": "A model that detects objects in images",
            "model_type": "computer_vision",
            "framework": "tensorflow",
            "version": "2.1.0",
            "created_at": "2023-02-20T00:00:00Z",
            "owner_id": "user456"
        }
    ]
    
    # Apply filters
    if model_type:
        models = [m for m in models if m["model_type"] == model_type]
    
    # Apply pagination
    models = models[skip:skip+limit]
    
    return models

@app.get(
    "/models/{model_id}",
    summary="Get model by ID",
    description="Get detailed information about a specific AI model",
    response_model=ModelInDB,
    tags=["models"],
    responses={
        200: {
            "description": "Successful Response",
            "content": {
                "application/json": {
                    "example": {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "name": "sentiment_analyzer",
                        "description": "A model for sentiment analysis of text",
                        "model_type": "nlp",
                        "framework": "pytorch",
                        "version": "1.0.0",
                        "created_at": "2023-01-15T00:00:00Z",
                        "owner_id": "user123"
                    }
                }
            }
        },
        404: {
            "description": "Model not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Model not found"}
                }
            }
        }
    }
)
def get_model(
    model_id: str = Path(
        ..., 
        title="Model ID", 
        description="The ID of the model to retrieve",
        example="123e4567-e89b-12d3-a456-426614174000"
    ),
    token: str = Depends(oauth2_scheme)
):
    """
    Get detailed information about a specific AI model by its ID.
    
    This endpoint requires authentication.
    """
    # In a real app, query model from database
    if model_id != "123e4567-e89b-12d3-a456-426614174000":
        raise HTTPException(status_code=404, detail="Model not found")
    
    return {
        "id": model_id,
        "name": "sentiment_analyzer",
        "description": "A model for sentiment analysis of text",
        "model_type": "nlp",
        "framework": "pytorch",
        "version": "1.0.0",
        "created_at": "2023-01-15T00:00:00Z",
        "owner_id": "user123"
    }

@app.post(
    "/models/",
    summary="Create a new model",
    description="Register a new AI model in the system",
    response_model=ModelInDB,
    status_code=status.HTTP_201_CREATED,
    tags=["models"]
)
def create_model(
    model: ModelCreate = Body(
        ...,
        title="Model Data",
        description="Data for creating a new AI model",
        example={
            "name": "new_classifier",
            "description": "A new classification model",
            "model_type": "classification",
            "framework": "sklearn",
            "version": "1.0.0",
            "training_data": "/data/training/dataset1/",
            "parameters": {"n_estimators": 100, "max_depth": 10}
        }
    ),
    token: str = Depends(oauth2_scheme)
):
    """
    Create a new AI model in the system.
    
    Provide all the necessary information about the model, including its training data path
    and parameters.
    
    This endpoint requires authentication.
    """
    # In a real app, save model to database
    model_id = str(uuid.uuid4())
    
    return {
        "id": model_id,
        "name": model.name,
        "description": model.description,
        "model_type": model.model_type,
        "framework": model.framework,
        "version": model.version,
        "created_at": "2023-03-01T00:00:00Z",
        "owner_id": "user123"  # In a real app, get from token
    }

@app.post(
    "/predictions/",
    summary="Make a prediction",
    description="Use an AI model to make a prediction on provided data",
    response_model=PredictionResponse,
    tags=["predictions"]
)
def create_prediction(
    prediction_request: PredictionRequest = Body(
        ...,
        title="Prediction Request",
        description="Data to make a prediction on and the model to use",
        example={
            "model_id": "123e4567-e89b-12d3-a456-426614174000",
            "data": {"text": "I love this product, it's amazing!"}
        }
    ),
    api_key: str = Depends(get_api_key)
):
    """
    Use an AI model to make a prediction on the provided data.
    
    Specify which model to use by its ID and provide the input data in the required format
    for that model.
    
    This endpoint requires an API key.
    """
    # In a real app, load model and make prediction
    model_id = prediction_request.model_id
    
    # Check if model exists
    if model_id != "123e4567-e89b-12d3-a456-426614174000":
        raise HTTPException(status_code=404, detail="Model not found")
    
    # Mock prediction
    return {
        "model_id": model_id,
        "prediction": {"sentiment": "positive", "class": 1},
        "confidence": 0.92,
        "execution_time": 0.023
    }

@app.post(
    "/users/",
    summary="Create a new user",
    description="Register a new user in the system",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["users"]
)
def create_user(
    user: UserCreate = Body(
        ...,
        title="User Data",
        description="Data for creating a new user",
    )
):
    """
    Register a new user in the system.
    
    The password will be securely hashed and not returned in the response.
    """
    # In a real app, hash password and save user to database
    user_id = str(uuid.uuid4())
    
    return {
        "id": user_id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name
    }

@app.get(
    "/users/me",
    summary="Get current user",
    description="Get information about the currently authenticated user",
    response_model=UserResponse,
    tags=["users"]
)
def read_users_me(token: str = Depends(oauth2_scheme)):
    """
    Get information about the currently authenticated user.
    
    This endpoint requires authentication.
    """
    # In a real app, decode token and get user from database
    return {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "username": "testuser",
        "email": "test@example.com",
        "full_name": "Test User"
    }

@app.get(
    "/admin/dashboard",
    summary="Admin dashboard",
    description="Get admin dashboard data (admin only)",
    tags=["admin"],
    include_in_schema=True
)
def admin_dashboard(
    x_admin_token: str = Header(
        ..., 
        title="Admin Token",
        description="Special token for admin access"
    )
):
    """
    Get data for the administrative dashboard.
    
    This endpoint is only accessible to administrators with a valid admin token.
    """
    if x_admin_token != "admin_secret_token":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    return {
        "user_count": 423,
        "model_count": 57,
        "prediction_count": 15243,
        "system_status": "healthy"
    }

@app.get(
    "/internal/debug",
    include_in_schema=False
)
def internal_debug():
    """This endpoint is not included in the API documentation."""
    return {"debug": "This is a debug endpoint"}

# Customize OpenAPI schema
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
        
    openapi_schema = get_openapi(
        title="AI Project API",
        version="1.0.0",
        description="API for AI model management and predictions",
        routes=app.routes,
    )
    
    # Add custom branding
    openapi_schema["info"]["x-logo"] = {
        "url": "https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png"
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# Practice Exercise Solution
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 