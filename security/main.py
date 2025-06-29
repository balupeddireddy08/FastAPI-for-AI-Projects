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

# =======================================================================
#
#  🏦 Welcome to SecureBank - A Simplified Security Demo 🏦
#
#  This FastAPI application demonstrates core security principles in a
#  clear and concise way, perfect for beginners. We've stripped away
#  complex business logic to focus purely on HOW to implement security.
#
#  Each section is numbered and explained to guide you through the concepts.
#
# =======================================================================

# --- 1. CORE SECURITY CONFIGURATION ---
# This is where we set up the fundamental tools for our security system.

# For hashing passwords. We use 'bcrypt', a strong, industry-standard algorithm.
# When a user signs up, we don't store their password "12345". Instead, we
# store the bcrypt hash, like "$2b$12$Eix...". This is a one-way process.
# If our database is ever stolen, the attackers can't see the real passwords.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# This is the secret key used to sign our JSON Web Tokens (JWTs).
# Think of it as the "master key" for our authentication system.
# The signature ensures that tokens haven't been tampered with.
# IMPORTANT: In a real app, this MUST be a long, random string loaded
# from a secure environment variable, not hardcoded!
SECRET_KEY = "a-very-secret-key-that-should-be-in-a-env-file"
ALGORITHM = "HS256"  # The specific cryptographic algorithm to sign the JWT.
ACCESS_TOKEN_EXPIRE_MINUTES = 30  # How long a token is valid after being issued.

# This object tells FastAPI two things about our login system:
# 1. It expects the client to send a token in the "Authorization" header
#    in the format "Bearer <token>".
# 2. It specifies the URL where the client can go to get a token (`/auth/login`).
#    FastAPI uses this for the interactive API docs (like Swagger UI).
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# We use 'slowapi' to implement rate limiting. This is a crucial defense
# against brute-force attacks, where an attacker tries to guess passwords
# by sending thousands of login requests per second.
# `get_remote_address` uses the client's IP address as a unique identifier.
limiter = Limiter(key_func=get_remote_address)


# --- 2. FASTAPI APP INITIALIZATION ---

app = FastAPI(
    title="🏦 SecureBank - Simplified Security Demo",
    description="""
    Learn FastAPI security with a simple banking example!

    This application demonstrates the following core security concepts:

    * 🔐 **Authentication**: Using JWT tokens for secure login. A user proves who they are.
    * 🛡️ **Authorization**: Using Role-Based Access Control (RBAC). Once authenticated, we check what the user is *allowed* to do.
    * 🔑 **Password Security**: Never storing plain text passwords by using strong hashing.
    * ⚡ **Rate Limiting**: Protecting login endpoints from automated brute-force attacks.
    * 📝 **Audit Logging**: Keeping a record of important security-related events.
    """,
    version="1.0.0"
)

# This is how we apply the rate limiter to our entire application.
# It also sets up a handler to automatically send a "429 Too Many Requests"
# error if a client exceeds the defined limits.
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# --- 3. DATA MODELS (PYDANTIC) ---
# Pydantic models define the structure and data types for our API.
# This is our first and most important line of defense for input validation.
# It automatically prevents many common vulnerabilities by ensuring
# that incoming data is in the correct format.

class UserRole(str, Enum):
    """
    Defines the roles a user can have. In a bank, different employees have
    different levels of access. An 'ADMIN' can do more than a 'CUSTOMER'.
    Using an Enum makes the roles explicit and less prone to typos.
    """
    CUSTOMER = "customer"
    ADMIN = "admin"

class User(BaseModel):
    """This is the basic, public-facing model for a user."""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr  # Pydantic automatically validates this is a valid email format.
    role: UserRole

class UserInDB(User):
    """
    This model represents a user as it is stored in our "database".
    It inherits from `User` and adds the `hashed_password`. We never want
    to expose the hashed password in API responses, so we keep it in a
    separate model.
    """
    hashed_password: str

class UserCreate(BaseModel):
    """
    This model is used specifically for the registration endpoint.
    It defines the data needed to create a new user, including the password.
    """
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)

class Token(BaseModel):
    """
    This model defines the structure of the response when a user logs in successfully.
    It contains the access token they will need for future requests.
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
# For the sake of simplicity in this demo, we're using simple Python
# dictionaries to act as our database. In a real-world application,
# this would be a proper database system like PostgreSQL, MySQL, or MongoDB.

# This dictionary will store our user data, with the username as the key.
db_users: Dict[str, UserInDB] = {}

# This list will store our audit log records.
audit_log: List[Dict] = []


# --- 5. SECURITY UTILITY FUNCTIONS ---
# These are helper functions that perform common security-related tasks.

def get_password_hash(password: str) -> str:
    """Hashes a plain-text password using the pre-configured pwd_context."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies a plain-text password against a hashed one.
    Returns True if they match, False otherwise. This is used during login.
    """
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict) -> str:
    """
    Creates a new JWT. It takes a dictionary of data to encode,
    adds an expiration timestamp, and then signs it with our SECRET_KEY.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    # The actual encoding and signing happens here.
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def log_security_event(event_type: str, username: Optional[str], request: Request, details: Dict):
    """
    A simple function to log important security events.
    In a real system, this would write to a dedicated logging service
    or a secure database table for auditing and monitoring.
    """
    audit_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": event_type,
        "username": username,
        "ip_address": request.client.host, # Tracks where the request came from.
        "details": details,
    }
    audit_log.append(audit_entry)


# --- 6. DEPENDENCIES FOR AUTHENTICATION & AUTHORIZATION ---
# Dependencies are a key feature of FastAPI. They are functions that run *before*
# your endpoint logic. We use them to handle repeated tasks like checking for
# a valid token or ensuring a user has the correct permissions.

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> UserInDB:
    """
    This is our main authentication dependency. It does the following:
    1. It depends on `oauth2_scheme`, which extracts the token from the request header.
    2. It tries to decode the token using our SECRET_KEY.
    3. If the token is invalid or expired, it raises an HTTP 401 Unauthorized error.
    4. If the token is valid, it retrieves the user from our "database".
    5. If the user exists, it returns the user object.

    Any endpoint that includes this as a dependency is now protected and requires a valid token.
    It's like the bank's security guard checking your ID card at the entrance.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Decode the token to get the payload
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        # Extract the username ("sub" is a standard JWT claim for "subject") and role
        username: str = payload.get("sub")
        role: str = payload.get("role")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username, role=role)
    except JWTError:
        # This will catch any errors from `jwt.decode`, like an invalid signature or expired token.
        raise credentials_exception

    # Find the user in our database
    user = db_users.get(token_data.username)
    if user is None:
        raise credentials_exception
    return user

def require_roles(required_roles: List[UserRole]):
    """
    This is a dependency *factory*. It's a function that returns another function (a dependency).
    We use this to create a flexible role-checking system for authorization.

    How it works:
    - You call it with a list of roles, e.g., `require_roles([UserRole.ADMIN])`.
    - It returns a `role_checker` dependency that "remembers" the required roles.
    - This `role_checker` is then used in an endpoint.

    This is our Role-Based Access Control (RBAC) system. It checks what a user is *allowed* to do.
    """
    def role_checker(current_user: Annotated[UserInDB, Depends(get_current_user)]):
        """
        This is the actual dependency that will be run by FastAPI.
        It first gets the `current_user` (ensuring authentication).
        Then, it checks if the user's role is in the list of required roles.
        If not, it raises an HTTP 403 Forbidden error.
        """
        if current_user.role not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {[role.value for role in required_roles]}"
            )
        return current_user
    return role_checker


# --- 7. API ENDPOINTS ---
# These are the actual URLs of our application.

@app.get("/")
def read_root():
    """A welcoming, public endpoint that anyone can access."""
    return {"message": "Welcome to SecureBank! See /docs for API documentation."}

@app.post("/auth/register", status_code=status.HTTP_201_CREATED, response_model=User)
async def register_user(user_data: UserCreate, request: Request):
    """
    🎉 **Concept: User Registration & Password Hashing**
    Creates a new user account. When a user sends their desired username and
    password, we immediately hash the password before storing the user's data.
    We never, ever store the plain-text password.
    """
    if user_data.username in db_users:
        raise HTTPException(status_code=400, detail="Username already registered")

    # Hash the password before creating the user record
    hashed_password = get_password_hash(user_data.password)
    user_in_db = UserInDB(
        username=user_data.username,
        email=user_data.email,
        role=UserRole.CUSTOMER,  # New users are customers by default.
        hashed_password=hashed_password
    )
    db_users[user_data.username] = user_in_db
    # Log this important security event.
    log_security_event("registration", user_data.username, request, {"email": user_data.email})

    return user_in_db


@app.post("/auth/login", response_model=Token)
@limiter.limit("5/minute")  # Apply rate limiting directly to the login endpoint.
async def login_for_access_token(
    request: Request,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
):
    """
    🔐 **Concepts: Authentication, JWT Creation, Rate Limiting**
    This is the login endpoint.
    - A user submits their username and password in a form.
    - We verify the password against the stored hash.
    - If successful, we create a new JWT access token and return it.
    - Rate limiting is applied here to prevent attackers from repeatedly
      trying to guess passwords (a brute-force attack).
    """
    # Note: `form_data` is a special dependency that handles OAuth2 password flows.
    user = db_users.get(form_data.username)
    # The `verify_password` function is crucial here for secure comparison.
    if not user or not verify_password(form_data.password, user.hashed_password):
        # Log the failed attempt for security monitoring.
        log_security_event("login_failed", form_data.username, request, {"reason": "invalid_credentials"})
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    # Create the JWT containing the user's identity (username and role).
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role.value}
    )
    log_security_event("login_success", user.username, request, {})

    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users/me", response_model=User)
async def read_users_me(current_user: Annotated[UserInDB, Depends(get_current_user)]):
    """
    👤 **Concept: Requiring Authentication**
    This is a protected endpoint. By including `Depends(get_current_user)`,
    we ensure that only authenticated users with a valid token can access it.
    FastAPI handles all the error-checking for us based on the dependency logic.
    It's like showing your ID to a bank teller to access your own account information.
    """
    return current_user


@app.get("/admin/audit-log")
async def get_audit_log(
    request: Request,
    # This is where we use our authorization dependency!
    current_user: Annotated[UserInDB, Depends(require_roles([UserRole.ADMIN]))]
):
    """
    📋 **Concept: Role-Based Access Control (RBAC)**
    This endpoint is not just protected, it's restricted.
    The `Depends(require_roles([UserRole.ADMIN]))` part ensures two things:
    1. The user must be authenticated (because `require_roles` calls `get_current_user`).
    2. The authenticated user must have the `ADMIN` role.
    If a regular customer tries to access this, they will get a 403 Forbidden error.
    This is like how only a bank manager is allowed to view the security camera footage.
    """
    log_security_event("audit_log_accessed", current_user.username, request, {})
    return {"audit_log": audit_log}

@app.get("/account/secret-details")
async def get_secret_details(current_user: Annotated[UserInDB, Depends(get_current_user)]):
    """
    🤫 **Concept: Placeholder for Multi-Factor Authentication (MFA)**
    In a real application, some actions are so sensitive (like transferring a
    large sum of money) that just a password isn't enough. This is where you
    would implement an MFA check (e.g., a code from an authenticator app).

    This endpoint simulates that. It's authenticated, but for a real-world
    version, you would add another dependency here to check if an MFA step
    has been recently and successfully completed.
    """
    # In a real implementation, you might have a flag on your user model.
    # mfa_enabled = getattr(current_user, 'mfa_enabled', False)
    # if not mfa_enabled:
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="MFA is required for this action."
    #     )
    return {
        "message": "You have accessed ultra-secret account details!",
        "details": "Your secret PIN is 1234. (Don't tell anyone!)",
        "note": "In a real app, this endpoint would be protected by an additional MFA check."
    }

# --- 8. RUN THE APPLICATION ---

# This standard Python block allows us to run the server directly
# for development by executing `python main.py`.
if __name__ == "__main__":
    import uvicorn
    # For demonstration purposes, we pre-populate our "database" with a demo
    # admin user. This way, we can immediately test the admin-only endpoints.
    if "admin" not in db_users:
        admin_user = UserInDB(
            username="admin",
            email="admin@securebank.com",
            role=UserRole.ADMIN,
            hashed_password=get_password_hash("AdminPass123!")
        )
        db_users["admin"] = admin_user
        print("Created demo admin user: username='admin', password='AdminPass123!'")

    print("🏦 Starting SecureBank Demo Platform...")
    uvicorn.run(app, host="0.0.0.0", port=8000) 