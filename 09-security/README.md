# 🏦 Section 9: Security - SecureBank Digital Banking Platform

Master **enterprise-grade security** by building a digital banking system! Learn authentication, authorization, data protection, rate limiting, and security best practices using FastAPI's comprehensive security features.

## 🎯 What You'll Learn

- JWT authentication and session management
- Role-based access control (RBAC)
- Password hashing and security best practices
- Rate limiting and DDoS protection
- Input validation and SQL injection prevention

## 🏦 Meet SecureBank Platform

Our banking system demonstrates security excellence through:

**Key Features:**
- 🔐 Multi-factor authentication (MFA)
- 💳 Secure payment processing
- 🏛️ Role-based permissions system
- 📊 Audit logging and monitoring
- 🛡️ Advanced threat protection

## 🚀 Core Security Concepts

### **1. Password Security**

```python
from passlib.context import CryptContext
from pydantic import BaseModel, Field, validator
import re

# Secure password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserRegistration(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str
    password: str = Field(..., min_length=8)
    confirm_password: str
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain lowercase letter')
        if not re.search(r'[0-9]', v):
            raise ValueError('Password must contain number')
        if not re.search(r'[!@#$%^&*(),.?\":{}|<>]', v):
            raise ValueError('Password must contain special character')
        return v
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
```

### **2. JWT Authentication**

```python
from datetime import datetime, timedelta
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer

SECRET_KEY = "your-secret-key-here"  # Use environment variable in production
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

security = HTTPBearer()

class TokenData(BaseModel):
    user_id: Optional[int] = None
    username: Optional[str] = None
    role: Optional[str] = None

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(security)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("user_id")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = get_user_by_id(user_id)
    if user is None:
        raise credentials_exception
    return user

@app.post("/auth/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"user_id": user.id, "username": user.username, "role": user.role},
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}
```

### **3. Role-Based Access Control**

```python
from enum import Enum
from functools import wraps

class UserRole(str, Enum):
    CUSTOMER = "customer"
    TELLER = "teller"
    MANAGER = "manager"
    ADMIN = "admin"

def require_role(required_role: UserRole):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user') or args[-1]
            
            role_hierarchy = {
                UserRole.CUSTOMER: 0,
                UserRole.TELLER: 1,
                UserRole.MANAGER: 2,
                UserRole.ADMIN: 3
            }
            
            if role_hierarchy[current_user.role] < role_hierarchy[required_role]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient permissions. {required_role} role required."
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

@app.get("/admin/users")
@require_role(UserRole.ADMIN)
async def get_all_users(current_user: User = Depends(get_current_user)):
    """Admin-only endpoint to view all users"""
    return get_users_from_database()

@app.post("/transactions/transfer")
@require_role(UserRole.CUSTOMER)
async def transfer_funds(
    transfer_data: TransferRequest,
    current_user: User = Depends(get_current_user)
):
    """Customer can transfer their own funds"""
    if transfer_data.from_account_id not in current_user.account_ids:
        raise HTTPException(status_code=403, detail="Unauthorized account access")
    
    return process_transfer(transfer_data, current_user.id)
```

## 🛡️ Advanced Security Features

### **1. Rate Limiting**

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/auth/login")
@limiter.limit("5/minute")  # Only 5 login attempts per minute per IP
async def login_with_rate_limit(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends()
):
    return await login(form_data)

@app.post("/transactions/transfer")
@limiter.limit("10/hour")  # Limit money transfers
async def transfer_with_limit(
    request: Request,
    transfer_data: TransferRequest,
    current_user: User = Depends(get_current_user)
):
    return await transfer_funds(transfer_data, current_user)
```

### **2. Input Validation and Sanitization**

```python
from pydantic import BaseModel, Field, validator
import re
from html import escape

class TransferRequest(BaseModel):
    from_account_id: str = Field(..., regex=r"^ACC[0-9]{10}$")
    to_account_id: str = Field(..., regex=r"^ACC[0-9]{10}$")
    amount: Decimal = Field(..., gt=0, le=10000)  # Max $10k per transfer
    description: Optional[str] = Field(None, max_length=200)
    
    @validator('description')
    def sanitize_description(cls, v):
        if v:
            # Remove HTML and escape special characters
            sanitized = escape(v.strip())
            # Remove any potential SQL injection patterns
            if re.search(r'(union|select|insert|update|delete|drop)', sanitized, re.IGNORECASE):
                raise ValueError('Invalid characters in description')
            return sanitized
        return v
    
    @validator('to_account_id')
    def validate_different_accounts(cls, v, values):
        if 'from_account_id' in values and v == values['from_account_id']:
            raise ValueError('Cannot transfer to the same account')
        return v

@app.post("/transactions/transfer")
async def secure_transfer(
    transfer_data: TransferRequest,
    current_user: User = Depends(get_current_user)
):
    # Additional business logic validation
    if not account_belongs_to_user(transfer_data.from_account_id, current_user.id):
        raise HTTPException(status_code=403, detail="Unauthorized account access")
    
    if not account_exists(transfer_data.to_account_id):
        raise HTTPException(status_code=404, detail="Destination account not found")
    
    return await process_secure_transfer(transfer_data, current_user)
```

### **3. Multi-Factor Authentication**

```python
import pyotp
import qrcode
from io import BytesIO
import base64

class MFASetup(BaseModel):
    user_id: int
    secret: str
    qr_code: str
    backup_codes: List[str]

@app.post("/auth/mfa/setup")
async def setup_mfa(current_user: User = Depends(get_current_user)):
    """Set up multi-factor authentication for user"""
    
    # Generate secret key
    secret = pyotp.random_base32()
    
    # Create TOTP instance
    totp = pyotp.TOTP(secret)
    
    # Generate QR code
    provisioning_uri = totp.provisioning_uri(
        name=current_user.username,
        issuer_name="SecureBank"
    )
    
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(provisioning_uri)
    qr.make(fit=True)
    
    # Convert QR code to base64 string
    img = qr.make_image(fill_color="black", back_color="white")
    buffered = BytesIO()
    img.save(buffered)
    qr_code_b64 = base64.b64encode(buffered.getvalue()).decode()
    
    # Generate backup codes
    backup_codes = [pyotp.random_base32()[:8] for _ in range(10)]
    
    # Save MFA settings to database
    save_mfa_settings(current_user.id, secret, backup_codes)
    
    return MFASetup(
        user_id=current_user.id,
        secret=secret,
        qr_code=qr_code_b64,
        backup_codes=backup_codes
    )

@app.post("/auth/mfa/verify")
async def verify_mfa(
    token: str,
    current_user: User = Depends(get_current_user)
):
    """Verify MFA token during login"""
    mfa_settings = get_mfa_settings(current_user.id)
    if not mfa_settings:
        raise HTTPException(status_code=400, detail="MFA not set up")
    
    totp = pyotp.TOTP(mfa_settings.secret)
    
    if totp.verify(token) or token in mfa_settings.backup_codes:
        if token in mfa_settings.backup_codes:
            # Remove used backup code
            remove_backup_code(current_user.id, token)
        
        return {"message": "MFA verification successful"}
    else:
        raise HTTPException(status_code=400, detail="Invalid MFA token")
```

## 📊 Security Monitoring

### **1. Audit Logging**

```python
import logging
from datetime import datetime
from typing import Optional

class AuditLog(BaseModel):
    user_id: Optional[int]
    action: str
    resource: str
    ip_address: str
    timestamp: datetime
    success: bool
    details: Optional[dict] = None

async def log_security_event(
    action: str,
    resource: str,
    request: Request,
    user_id: Optional[int] = None,
    success: bool = True,
    details: Optional[dict] = None
):
    """Log security-related events"""
    audit_entry = AuditLog(
        user_id=user_id,
        action=action,
        resource=resource,
        ip_address=get_client_ip(request),
        timestamp=datetime.utcnow(),
        success=success,
        details=details
    )
    
    # Save to database and send to monitoring system
    await save_audit_log(audit_entry)
    await send_to_security_monitoring(audit_entry)

@app.post("/auth/login")
async def login_with_audit(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends()
):
    try:
        result = await login(form_data)
        
        # Log successful login
        await log_security_event(
            action="LOGIN_SUCCESS",
            resource="auth",
            request=request,
            user_id=result.get("user_id"),
            success=True
        )
        
        return result
        
    except HTTPException as e:
        # Log failed login attempt
        await log_security_event(
            action="LOGIN_FAILED",
            resource="auth",
            request=request,
            success=False,
            details={"error": str(e.detail), "username": form_data.username}
        )
        raise
```

## 🎮 Key Security Endpoints

### **Authentication & Authorization**
```python
@app.post("/auth/register", response_model=UserResponse)
async def register_user(user_data: UserRegistration)

@app.post("/auth/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends())

@app.post("/auth/logout")
async def logout(current_user: User = Depends(get_current_user))

@app.post("/auth/change-password")
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user)
)
```

### **Secure Operations**
```python
@app.post("/transactions/transfer")
@require_role(UserRole.CUSTOMER)
@limiter.limit("10/hour")
async def transfer_funds(transfer_data: TransferRequest)

@app.get("/accounts/{account_id}/balance")
@require_role(UserRole.CUSTOMER)
async def get_account_balance(account_id: str)

@app.get("/admin/audit-logs")
@require_role(UserRole.ADMIN)
async def get_audit_logs(page: int = 1, limit: int = 50)
```

## 🛠️ Running SecureBank

```bash
cd 09-security
uvicorn main:app --reload

# Test security features:
# POST /auth/register (create account)
# POST /auth/login (authenticate)
# POST /auth/mfa/setup (enable MFA)
# POST /transactions/transfer (secure transfer)
```

## 📊 Security Checklist

| Security Feature | Implementation | Status |
|------------------|----------------|--------|
| **Password Hashing** | bcrypt with salt | ✅ Implemented |
| **JWT Authentication** | Secure tokens with expiry | ✅ Implemented |
| **Role-Based Access** | Hierarchical permissions | ✅ Implemented |
| **Rate Limiting** | Per-endpoint limits | ✅ Implemented |
| **Input Validation** | Pydantic + sanitization | ✅ Implemented |
| **MFA Support** | TOTP + backup codes | ✅ Implemented |
| **Audit Logging** | All actions logged | ✅ Implemented |

## 🎮 Practice Exercises

1. **🔐 API Key Management**: Implement API key authentication
2. **🛡️ WAF Integration**: Add Web Application Firewall rules
3. **📊 Fraud Detection**: Build real-time transaction monitoring
4. **🔒 Data Encryption**: Add field-level encryption for sensitive data

## 💡 Security Best Practices

### **Authentication**
- Use strong password requirements
- Implement account lockout after failed attempts
- Add MFA for sensitive operations
- Use secure session management

### **Authorization**
- Follow principle of least privilege
- Implement role-based access control
- Validate permissions on every request
- Log all authorization failures

### **Data Protection**
- Encrypt sensitive data at rest
- Use HTTPS for all communications
- Sanitize all user inputs
- Implement proper error handling

## 🚀 What's Next?

In **Section 10: AI Integration**, we'll build an AI-powered assistant platform that shows how to integrate LangChain, Google Gemini, and other AI services securely!

**Key Takeaway**: Security is not optional - it's the foundation that makes everything else possible. Build security in from day one! 🏦🔒 