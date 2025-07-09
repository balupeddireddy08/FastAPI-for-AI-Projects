import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Annotated

from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr, Field
from enum import Enum

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi.responses import HTMLResponse

# =======================================================================
#
#  🎟️ Welcome to the Secure Concert API - A Simplified Security Demo 🎟️
#
#  This FastAPI application demonstrates core security principles in a
#  clear and concise way, using a "concert ticket" analogy. We've
#  stripped away complex logic to focus purely on HOW to implement security.
#
#  Each section is numbered and explained to guide you through the concepts.
#
# =======================================================================

# --- 1. CORE SECURITY CONFIGURATION ---
# This is where we set up the fundamental tools for our security system.

# For hashing passwords. We use 'bcrypt', a strong, industry-standard algorithm.
# When a user registers for a ticket, we don't store their password "12345".
# Instead, we store the bcrypt hash, like "$2b$12$Eix...". This is a one-way process.
# If our database is ever stolen, the attackers can't see the real passwords.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# This is the secret key used to sign our JSON Web Tokens (JWTs).
#
# JWT (JSON Web Token) and Bearer Token Explained:
# Imagine a JWT is your digital concert ticket. When you log in (get your ticket),
# the server gives you this ticket, which contains who you are, when it expires,
# and a special digital seal (signature) using this SECRET_KEY.
# This seal proves the ticket is genuine and untampered.
#
# The "Bearer Token" concept is how you present this ticket. For future requests to protected areas
# (like getting backstage access), you send your JWT in the "Authorization" header
# like "Authorization: Bearer <YOUR_JWT>".
# "Bearer" simply means "The holder of this token is authorized."
SECRET_KEY = "a-very-secret-key-that-should-be-in-a-env-file"
ALGORITHM = "HS256"  # The specific cryptographic algorithm to sign the JWT.
ACCESS_TOKEN_EXPIRE_MINUTES = 30  # How long a token is valid after being issued.

# This object tells FastAPI two things about our login system:
# 1. It expects the client to send a token in the "Authorization" header
#    in the format "Bearer <token>".
# 2. It specifies the URL where the client can go to get a token (`/auth/login`).
#    This is used by the interactive API docs (Swagger UI).
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# We use 'slowapi' to implement rate limiting. This is a crucial defense
# against brute-force attacks, where an attacker tries to guess passwords
# by sending thousands of login requests per second.
limiter = Limiter(key_func=get_remote_address)


# --- 2. FASTAPI APP INITIALIZATION ---

app = FastAPI(
    title="🎟️ Secure Concert API - Simplified Security Demo",
    description="""
    Learn FastAPI security with a simple concert ticket example!

    This application demonstrates the following core security concepts:

    * 🔐 **Authentication**: Using JWTs as "digital tickets" for secure login. A user proves who they are.
    * 🛡️ **Authorization**: Using Role-Based Access Control (RBAC). Once authenticated, we check what the user is *allowed* to do (e.g., access the guest list).
    * 🔑 **Password Security**: Never storing plain text passwords by using strong hashing.
    * ⚡ **Rate Limiting**: Protecting login endpoints from automated brute-force attacks.
    """,
    version="1.0.0"
)

# Apply the rate limiter to our entire application.
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# --- 3. DATA MODELS (PYDANTIC) ---
# Pydantic models define the structure and data types for our API.
# This provides automatic input validation, preventing many common vulnerabilities.

class UserRole(str, Enum):
    """
    Defines the roles a user can have. An 'ORGANIZER' can do more than a 'GUEST'.
    Using an Enum makes the roles explicit and less prone to typos.
    """
    GUEST = "guest"
    ORGANIZER = "organizer"

class User(BaseModel):
    """This is the basic, public-facing model for a user (an attendee)."""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    role: UserRole

class UserInDB(User):
    """
    This model represents a user as it is stored in our "database".
    It inherits from `User` and adds the `hashed_password`. We never expose
    the hashed password in API responses, so we keep it in a separate model.
    """
    hashed_password: str

class UserCreate(BaseModel):
    """
    This model is used specifically for the registration endpoint.
    It defines the data needed to create a new user.
    """
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)

class Token(BaseModel):
    """
    This model defines the structure of the response when a user logs in successfully.
    It contains the access token (their digital ticket).
    """
    access_token: str
    token_type: str

class TokenData(BaseModel):
    """
    This model represents the data that is encoded *inside* a JWT.
    It's what we get back after we decode a valid token.
    """
    username: Optional[str] = None
    role: Optional[UserRole] = None


# --- 4. IN-MEMORY "DATABASE" ---
# For simplicity, we're using a simple Python dictionary as our database.
# In a real-world application, this would be a proper database like PostgreSQL.

db_users: Dict[str, UserInDB] = {}


# --- 5. SECURITY UTILITY FUNCTIONS ---
# These are helper functions that perform common security-related tasks.

def get_password_hash(password: str) -> str:
    """Hashes a plain-text password."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain-text password against a hashed one. Used during login."""
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict) -> str:
    """
    Creates a new JWT (digital ticket). It encodes the data, adds an
    expiration timestamp, and then signs it with our SECRET_KEY.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# --- 6. DEPENDENCIES FOR AUTHENTICATION & AUTHORIZATION ---
# Dependencies run *before* your endpoint logic. We use them to check for
# a valid token or ensure a user has the correct permissions.

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> UserInDB:
    """
    This is our main authentication dependency. It's the security guard at the concert entrance.
    1. It extracts the token (the ticket) from the request header.
    2. It tries to decode the token using our SECRET_KEY to check its signature.
    3. If the token is invalid, expired, or forged, it raises an HTTP 401 error.
    4. If the token is valid, it retrieves the user from our "database".
    5. It returns the user object, granting them access.

    Any endpoint with this dependency is now protected.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        role: str = payload.get("role")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username, role=role)
    except JWTError:
        raise credentials_exception

    user = db_users.get(token_data.username)
    if user is None:
        raise credentials_exception
    return user

# This dependency is a simple way to require a specific role.
# It uses `get_current_user` to get the authenticated user first,
# and then checks if their role is in the list of allowed roles.
def require_roles(required_roles: List[UserRole]):
    def role_checker(current_user: Annotated[UserInDB, Depends(get_current_user)]):
        if current_user.role not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. User does not have one of the required roles: {', '.join(r.value for r in required_roles)}",
            )
        return current_user
    return role_checker


# --- 7. API ENDPOINTS ---
# These are the actual pages of our API.

@app.get("/", response_class=HTMLResponse)
def read_root():
    """
    Serves the main HTML page for the demo.
    """
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()


@app.post("/auth/register", status_code=status.HTTP_201_CREATED, response_model=User)
async def register_user(user_data: UserCreate, request: Request):
    """
    🎉 **Concept: User Registration & Password Hashing**
    Creates a new user account (registers them for the event). We immediately
    hash the password before storing the user's data.
    """
    if user_data.username in db_users:
        raise HTTPException(status_code=400, detail="Username already registered")

    hashed_password = get_password_hash(user_data.password)
    user_in_db = UserInDB(
        username=user_data.username,
        email=user_data.email,
        role=UserRole.GUEST,  # New users are guests by default.
        hashed_password=hashed_password
    )
    db_users[user_data.username] = user_in_db
    return user_in_db


@app.post("/auth/login", response_model=Token)
@limiter.limit("5/minute")
async def login_for_access_token(
    request: Request,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
):
    """
    🔐 **Concepts: Authentication, JWT Creation, Rate Limiting**
    This is the login endpoint where a user gets their JWT (digital ticket).
    - We verify the username and password.
    - If successful, we create a new JWT and return it.
    - Rate limiting prevents brute-force attacks (someone trying to guess passwords).
    """
    user = db_users.get(form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    access_token = create_access_token(
        data={"sub": user.username, "role": user.role.value}
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/attendees/me", response_model=User)
async def read_users_me(current_user: Annotated[UserInDB, Depends(get_current_user)]):
    """
    👤 **Concept: Requiring Authentication**
    This is a protected endpoint. Including `Depends(get_current_user)`
    ensures that only authenticated users with a valid ticket (JWT) can see
    their own details.
    """
    return current_user


@app.get("/organizer/guest-list")
async def get_guest_list(
    current_user: Annotated[UserInDB, Depends(require_roles([UserRole.ORGANIZER]))]
):
    """
    📋 **Concept: Role-Based Access Control (RBAC)**
    This endpoint is restricted. The `Depends(require_roles([UserRole.ORGANIZER]))`
    part ensures that only users with the `ORGANIZER` role can access it.
    A regular `GUEST` will get a 403 Forbidden error.
    """
    return {"guest_list": [user.username for user in db_users.values()]}


# --- 8. RUN THE APPLICATION ---

if __name__ == "__main__":
    import uvicorn
    # Pre-populate our "database" with a demo organizer user
    # so we can immediately test the organizer-only endpoints.
    if "organizer" not in db_users:
        organizer_user = UserInDB(
            username="organizer",
            email="organizer@concert.com",
            role=UserRole.ORGANIZER,
            hashed_password=get_password_hash("OrganizerPass123!")
        )
        db_users["organizer"] = organizer_user
        print("Created demo organizer user: username='organizer', password='OrganizerPass123!'")

    print("🎟️ Starting Secure Concert API...")
    uvicorn.run(app, host="0.0.0.0", port=8000) 