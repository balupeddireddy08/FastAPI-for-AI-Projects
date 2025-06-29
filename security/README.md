# 🏦 Section 9: Security - A Simplified Introduction

Welcome to a beginner-friendly guide to **enterprise-grade security** in FastAPI! We'll explore the most important security concepts by building a simplified digital banking system, SecureBank. This guide focuses on clarity and understanding, stripping away complex logic to highlight the core security features.

## 🎯 What You'll Learn

-   **JWT Authentication**: How to issue and validate tokens for secure logins.
-   **Role-Based Access Control (RBAC)**: How to restrict access to certain endpoints based on user roles (e.g., "admin" vs. "customer").
-   **Password Hashing**: Why we never store plain-text passwords and how to hash them securely.
-   **Rate Limiting**: How to protect your API from simple brute-force attacks.
-   **Audit Logging**: The importance of keeping a log of important security events.

## 🏦 Meet the Simplified SecureBank Platform

Our simplified banking system demonstrates these core security concepts:

-   🔐 **User Registration**: Securely creating a user with a hashed password.
-   🔑 **User Login**: Authenticating a user and issuing a JWT access token.
-   🛡️ **Protected Endpoints**: Endpoints that require a valid token to access.
-   👑 **Admin-Only Access**: An endpoint that can only be accessed by a user with the "admin" role.

## 🚀 Core Security Concepts in Practice

### **1. Password Security with `passlib`**

We never store user passwords directly. Instead, we store a secure hash. This means even if our database is compromised, attackers cannot retrieve user passwords.

```python
from passlib.context import CryptContext

# Use bcrypt for strong, industry-standard password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    """Generates a hash from a plain-text password."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Checks if a plain-text password matches a stored hash."""
    return pwd_context.verify(plain_password, hashed_password)
```

### **2. JWT Authentication with `jose`**

After a user logs in, we give them a JSON Web Token (JWT). They must include this token in the header of future requests to prove who they are. The token is digitally signed to prevent tampering.

```python
from datetime import datetime, timedelta
from jose import jwt

SECRET_KEY = "your-secret-key"  # This should be a long, random string from an env var
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(data: dict) -> str:
    """Creates a signed JWT for a user."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
```

### **3. Getting the Current User (Authentication)**

This FastAPI dependency is the heart of our authentication system. It decodes the token from the request header to identify the user. Any endpoint that uses this dependency is automatically protected.

```python
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Decodes token, validates user, and returns user data."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            # Raise an error if the token is invalid
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    # In a real app, you'd fetch the user from a database here
    user = get_user_from_db(username) 
    if user is None:
        raise credentials_exception
    return user
```

### **4. Role-Based Access Control (Authorization)**

Authorization checks what a user is *allowed* to do. This dependency factory allows us to protect endpoints so they can only be accessed by users with specific roles.

```python
from enum import Enum

class UserRole(str, Enum):
    CUSTOMER = "customer"
    ADMIN = "admin"

def require_roles(required_roles: List[UserRole]):
    """A dependency to ensure a user has one of the required roles."""
    def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role not in required_roles:
            raise HTTPException(
                status_code=403, 
                detail="Access denied."
            )
        return current_user
    return role_checker

# Example of protecting an admin-only endpoint
@app.get("/admin/data")
async def get_admin_data(
    current_user: User = Depends(require_roles([UserRole.ADMIN]))
):
    return {"message": "This is secret admin data!"}
```

## 🛠️ Running the Simplified SecureBank Demo

To get started and see these concepts in action, follow these steps:

1.  **Navigate to the directory:**
    ```bash
    cd security
    ```

2.  **Install the required packages:**
    You'll need `fastapi`, `uvicorn`, `passlib[bcrypt]`, `python-jose[cryptography]`, and `slowapi`.
    ```bash
    pip install "fastapi[all]" "passlib[bcrypt]" "python-jose[cryptography]" "slowapi"
    ```

3.  **Run the application:**
    ```bash
    uvicorn main:app --reload
    ```
    The server will start, and you can access the API at `http://127.0.0.1:8000`.

## 🎮 How to Test the API

Open your browser to `http://127.0.0.1:8000/docs` to see the interactive API documentation (Swagger UI).

1.  **Register a New User**:
    -   Go to the `POST /auth/register` endpoint.
    -   Click "Try it out" and create a user (e.g., `username`: "testuser", `password`: "Str0ngP@ss!").

2.  **Log In to Get a Token**:
    -   Go to `POST /auth/login`.
    -   Enter the credentials you just created.
    -   On success, you will receive an `access_token`. Copy this token.

3.  **Access a Protected Endpoint**:
    -   Go to `GET /users/me`.
    -   Click the "Authorize" button at the top of the page.
    -   In the popup, paste your token in the format `Bearer <YOUR_TOKEN>`.
    -   Now, execute the endpoint. You should see your user details.

4.  **Test Admin Access (Failure)**:
    -   Try to access `GET /admin/audit-log`. It will fail with a `403 Forbidden` error because your user is a "customer", not an "admin".

5.  **Test Admin Access (Success)**:
    -   Log in with the pre-created admin user (`username`: "admin", `password`: "AdminPass123!").
    -   Get the new token and authorize with it.
    -   Now, try `GET /admin/audit-log` again. It will succeed!

**Key Takeaway**: Security isn't an afterthought. By understanding these core principles, you can build robust and secure applications from day one. 🏦🔒 