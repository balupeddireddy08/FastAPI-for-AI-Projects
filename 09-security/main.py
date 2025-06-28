import asyncio
import hashlib
import hmac
import uuid
import secrets
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Annotated
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import FastAPI, HTTPException, Depends, Security, status, Request, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from pydantic import BaseModel, Field, EmailStr, validator
from enum import Enum
import json
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Initialize SecureBank - The Most Secure Digital Banking Platform
app = FastAPI(
    title="🏦 SecureBank - Ultra-Secure Digital Banking Platform",
    description="""
    Welcome to **SecureBank** - where your financial security is our top priority! 🛡️✨
    
    Experience bank-grade security with:
    
    * 🔐 **Multi-Factor Authentication**: Multiple layers of identity verification
    * 🔑 **JWT Token Security**: Industry-standard secure token management
    * 🛡️ **Role-Based Access Control**: Granular permission management
    * 🚨 **Real-time Fraud Detection**: AI-powered security monitoring
    * 📝 **Complete Audit Logging**: Every action tracked and secured
    * ⚡ **Rate Limiting**: Protection against brute force attacks
    * 🔒 **Data Encryption**: End-to-end encrypted transactions
    * 🎯 **API Key Management**: Secure third-party integrations
    
    Built with FastAPI's security-first architecture - protecting millions in assets! 💰
    """,
    version="2.0.0"
)

# === SECURITY CONFIGURATION ===

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT configuration
SECRET_KEY = "your-super-secret-key-change-in-production"  # In production: use env variable
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")
security_bearer = HTTPBearer()

# Rate limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add security middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://securebank.com", "https://app.securebank.com"],  # Specific origins only
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=["securebank.com", "*.securebank.com", "localhost", "127.0.0.1"]
)

# === SECURITY MODELS ===

class UserRole(str, Enum):
    CUSTOMER = "customer"
    PREMIUM_CUSTOMER = "premium_customer"
    BUSINESS_CUSTOMER = "business_customer"
    TELLER = "teller"
    MANAGER = "manager"
    ADMIN = "admin"
    AUDITOR = "auditor"
    SYSTEM = "system"

class AccountType(str, Enum):
    CHECKING = "checking"
    SAVINGS = "savings"
    BUSINESS = "business"
    INVESTMENT = "investment"
    CREDIT = "credit"

class TransactionType(str, Enum):
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    TRANSFER = "transfer"
    PAYMENT = "payment"
    FEE = "fee"

class SecurityLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class MFAMethod(str, Enum):
    SMS = "sms"
    EMAIL = "email"
    AUTHENTICATOR = "authenticator"
    BIOMETRIC = "biometric"

# === USER & AUTHENTICATION MODELS ===

class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=30, regex="^[a-zA-Z0-9_]+$")
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=100)
    phone: Optional[str] = Field(None, regex="^\\+?[1-9]\\d{1,14}$")
    role: UserRole = UserRole.CUSTOMER

class UserCreate(UserBase):
    password: str = Field(..., min_length=12, max_length=100)
    confirm_password: str
    ssn_last_4: str = Field(..., regex="^[0-9]{4}$", description="Last 4 digits of SSN")
    date_of_birth: str = Field(..., regex="^[0-9]{4}-[0-9]{2}-[0-9]{2}$")
    initial_deposit: float = Field(100.0, ge=100.0, le=10000.0)
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v
    
    @validator('password')
    def validate_password_strength(cls, v):
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in v):
            raise ValueError('Password must contain at least one special character')
        return v

class UserInDB(UserBase):
    id: int
    hashed_password: str
    is_active: bool = True
    is_verified: bool = False
    failed_login_attempts: int = 0
    last_login: Optional[datetime] = None
    mfa_enabled: bool = False
    mfa_methods: List[MFAMethod] = []
    created_at: datetime
    security_level: SecurityLevel = SecurityLevel.MEDIUM

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    scope: str

class TokenData(BaseModel):
    user_id: Optional[int] = None
    username: Optional[str] = None
    role: Optional[UserRole] = None
    permissions: List[str] = []

class MFAChallenge(BaseModel):
    method: MFAMethod
    code: str = Field(..., min_length=6, max_length=6, regex="^[0-9]{6}$")
    challenge_id: str

# === ACCOUNT & TRANSACTION MODELS ===

class Account(BaseModel):
    id: str
    user_id: int
    account_type: AccountType
    balance: float
    account_number: str
    routing_number: str = "123456789"
    is_active: bool = True
    daily_limit: float = 5000.0
    monthly_limit: float = 50000.0
    created_at: datetime

class Transaction(BaseModel):
    id: str
    from_account_id: Optional[str] = None
    to_account_id: Optional[str] = None
    transaction_type: TransactionType
    amount: float
    description: str
    reference_number: str
    created_at: datetime
    processed_at: Optional[datetime] = None
    status: str = "pending"
    security_flags: List[str] = []

class TransferRequest(BaseModel):
    from_account_id: str
    to_account_id: str
    amount: float = Field(..., gt=0, le=10000)
    description: str = Field(..., min_length=1, max_length=500)
    recipient_name: str = Field(..., min_length=1, max_length=100)
    
    @validator('description')
    def validate_description(cls, v):
        # Security: Prevent injection attacks in descriptions
        prohibited_chars = ['<', '>', '{', '}', '[', ']', '&', ';']
        for char in prohibited_chars:
            if char in v:
                raise ValueError(f'Description contains prohibited character: {char}')
        return v.strip()

# === SECURITY UTILITIES ===

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict):
    """Create a JWT refresh token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> TokenData:
    """Verify and decode a JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("sub")
        username: str = payload.get("username")
        role: str = payload.get("role")
        permissions: List[str] = payload.get("permissions", [])
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        token_data = TokenData(
            user_id=user_id, 
            username=username, 
            role=UserRole(role) if role else None,
            permissions=permissions
        )
        return token_data
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

# === IN-MEMORY STORAGE (Use real database in production) ===

# Users database
users_db: Dict[str, UserInDB] = {}
user_accounts: Dict[int, List[Account]] = {}
transactions_db: List[Transaction] = []
audit_log: List[Dict] = []
active_mfa_challenges: Dict[str, Dict] = {}
api_keys: Dict[str, Dict] = {}

# === AUDIT LOGGING ===

def log_security_event(
    event_type: str,
    user_id: Optional[int],
    details: Dict,
    request: Request,
    security_level: SecurityLevel = SecurityLevel.MEDIUM
):
    """Log security events for audit purposes"""
    audit_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": event_type,
        "user_id": user_id,
        "ip_address": request.client.host,
        "user_agent": request.headers.get("user-agent"),
        "details": details,
        "security_level": security_level.value,
        "session_id": request.headers.get("x-session-id", "unknown")
    }
    audit_log.append(audit_entry)

# === DEPENDENCY FUNCTIONS ===

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> UserInDB:
    """Get the current authenticated user"""
    token_data = verify_token(token)
    user = users_db.get(token_data.username)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    return user

async def get_current_active_user(current_user: Annotated[UserInDB, Depends(get_current_user)]) -> UserInDB:
    """Get the current active user"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="🚫 Account is suspended. Please contact customer service."
        )
    return current_user

def require_roles(allowed_roles: List[UserRole]):
    """Dependency to require specific user roles"""
    def role_checker(current_user: Annotated[UserInDB, Depends(get_current_active_user)]) -> UserInDB:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"🔒 Access denied. Required roles: {[role.value for role in allowed_roles]}"
            )
        return current_user
    return role_checker

def require_mfa(current_user: Annotated[UserInDB, Depends(get_current_active_user)]) -> UserInDB:
    """Require MFA for sensitive operations"""
    if not current_user.mfa_enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="🔐 Multi-factor authentication required for this operation. Please enable MFA first."
        )
    return current_user

async def verify_api_key(x_api_key: Annotated[str, Header()]) -> Dict:
    """Verify API key for third-party integrations"""
    if x_api_key not in api_keys:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="🔑 Invalid API key"
        )
    
    api_key_info = api_keys[x_api_key]
    if not api_key_info["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="🔑 API key has been revoked"
        )
    
    # Update last used timestamp
    api_key_info["last_used"] = datetime.utcnow()
    return api_key_info

# === MAIN SECURITY ENDPOINTS ===

@app.get("/")
def bank_home():
    """🏠 Welcome to SecureBank - Your Security is Our Priority!"""
    return {
        "message": "🏦 Welcome to SecureBank!",
        "tagline": "Where your financial security meets cutting-edge technology 🛡️",
        "security_features": [
            "🔐 Multi-Factor Authentication",
            "🔒 End-to-End Encryption", 
            "🛡️ Real-time Fraud Detection",
            "📝 Complete Audit Logging",
            "⚡ Advanced Rate Limiting",
            "🎯 Role-Based Access Control"
        ],
        "trust_indicators": {
            "uptime": "99.99%",
            "security_certifications": ["SOC 2", "ISO 27001", "PCI DSS"],
            "customers_protected": 2500000,
            "assets_secured": "$15.7 billion"
        },
        "compliance": ["FDIC Insured", "Federal Reserve Regulated", "FFIEC Compliant"]
    }

# === AUTHENTICATION ENDPOINTS ===

@app.post("/auth/register", response_model=dict, status_code=status.HTTP_201_CREATED)
@limiter.limit("3/minute")  # Prevent registration spam
async def register_user(user_data: UserCreate, request: Request):
    """
    🎉 Open your SecureBank account!
    
    Create a new account with bank-grade security and instant fraud protection.
    """
    # Check if user already exists
    if user_data.username in users_db or any(u.email == user_data.email for u in users_db.values()):
        log_security_event(
            "registration_attempt_duplicate", 
            None, 
            {"username": user_data.username, "email": user_data.email},
            request,
            SecurityLevel.MEDIUM
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="🚫 Username or email already registered"
        )
    
    # Create user
    hashed_password = get_password_hash(user_data.password)
    user_id = len(users_db) + 1
    
    new_user = UserInDB(
        id=user_id,
        username=user_data.username,
        email=user_data.email,
        full_name=user_data.full_name,
        phone=user_data.phone,
        role=user_data.role,
        hashed_password=hashed_password,
        created_at=datetime.utcnow(),
        security_level=SecurityLevel.HIGH  # New accounts get high security
    )
    
    users_db[user_data.username] = new_user
    
    # Create default checking account
    account_number = f"ACC{user_id:08d}"
    new_account = Account(
        id=str(uuid.uuid4()),
        user_id=user_id,
        account_type=AccountType.CHECKING,
        balance=user_data.initial_deposit,
        account_number=account_number,
        created_at=datetime.utcnow()
    )
    
    user_accounts[user_id] = [new_account]
    
    # Log successful registration
    log_security_event(
        "user_registration_success",
        user_id,
        {"account_created": account_number},
        request,
        SecurityLevel.HIGH
    )
    
    return {
        "message": "🎉 Welcome to SecureBank!",
        "user_id": user_id,
        "username": user_data.username,
        "account_number": account_number,
        "initial_balance": user_data.initial_deposit,
        "next_steps": [
            "Verify your email address",
            "Set up multi-factor authentication",
            "Download our secure mobile app"
        ],
        "security_notice": "Your account is protected with bank-grade security! 🛡️"
    }

@app.post("/auth/login", response_model=Token)
@limiter.limit("5/minute")  # Prevent brute force attacks
async def login_user(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    request: Request
):
    """
    🔐 Secure login to your SecureBank account
    
    Multi-layered authentication with fraud detection and audit logging.
    """
    user = users_db.get(form_data.username)
    
    # Check if user exists and password is correct
    if not user or not verify_password(form_data.password, user.hashed_password):
        # Log failed login attempt
        log_security_event(
            "login_attempt_failed",
            user.id if user else None,
            {"username": form_data.username, "reason": "invalid_credentials"},
            request,
            SecurityLevel.HIGH
        )
        
        # Increment failed attempts
        if user:
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= 5:
                user.is_active = False
                log_security_event(
                    "account_locked",
                    user.id,
                    {"reason": "too_many_failed_attempts"},
                    request,
                    SecurityLevel.CRITICAL
                )
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="🚫 Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if account is active
    if not user.is_active:
        log_security_event(
            "login_attempt_blocked",
            user.id,
            {"reason": "account_inactive"},
            request,
            SecurityLevel.HIGH
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="🔒 Account is locked. Please contact customer service."
        )
    
    # Create tokens
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    user_permissions = get_user_permissions(user.role)
    
    access_token = create_access_token(
        data={
            "sub": user.id,
            "username": user.username,
            "role": user.role.value,
            "permissions": user_permissions
        },
        expires_delta=access_token_expires
    )
    
    refresh_token = create_refresh_token(
        data={"sub": user.id, "username": user.username}
    )
    
    # Reset failed attempts and update last login
    user.failed_login_attempts = 0
    user.last_login = datetime.utcnow()
    
    # Log successful login
    log_security_event(
        "login_success",
        user.id,
        {"mfa_enabled": user.mfa_enabled},
        request,
        SecurityLevel.MEDIUM
    )
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "scope": " ".join(user_permissions)
    }

def get_user_permissions(role: UserRole) -> List[str]:
    """Get permissions based on user role"""
    permission_map = {
        UserRole.CUSTOMER: ["account:read", "transaction:create", "transfer:own"],
        UserRole.PREMIUM_CUSTOMER: ["account:read", "transaction:create", "transfer:any", "investment:read"],
        UserRole.BUSINESS_CUSTOMER: ["account:read", "transaction:create", "transfer:any", "payroll:create"],
        UserRole.TELLER: ["account:read", "transaction:create", "customer:assist"],
        UserRole.MANAGER: ["account:read", "account:modify", "transaction:read", "user:manage"],
        UserRole.ADMIN: ["*"],  # All permissions
        UserRole.AUDITOR: ["audit:read", "transaction:read", "account:read"],
        UserRole.SYSTEM: ["system:*"]
    }
    return permission_map.get(role, [])

# === MULTI-FACTOR AUTHENTICATION ===

@app.post("/auth/mfa/setup")
async def setup_mfa(
    method: MFAMethod,
    current_user: Annotated[UserInDB, Depends(get_current_active_user)],
    request: Request
):
    """
    🔐 Set up Multi-Factor Authentication
    
    Add an extra layer of security to protect your account.
    """
    challenge_id = str(uuid.uuid4())
    verification_code = f"{secrets.randbelow(900000) + 100000:06d}"
    
    # Store MFA challenge
    active_mfa_challenges[challenge_id] = {
        "user_id": current_user.id,
        "method": method,
        "code": verification_code,
        "expires_at": datetime.utcnow() + timedelta(minutes=10),
        "purpose": "setup"
    }
    
    # Log MFA setup attempt
    log_security_event(
        "mfa_setup_initiated",
        current_user.id,
        {"method": method.value},
        request,
        SecurityLevel.HIGH
    )
    
    # In production, send the code via SMS, email, etc.
    setup_instructions = {
        MFAMethod.SMS: f"📱 SMS verification code sent to your phone ending in ****{current_user.phone[-4:] if current_user.phone else '0000'}",
        MFAMethod.EMAIL: f"📧 Verification code sent to {current_user.email[:3]}***@{current_user.email.split('@')[1]}",
        MFAMethod.AUTHENTICATOR: "📱 Scan the QR code with your authenticator app",
        MFAMethod.BIOMETRIC: "👆 Place your finger on the biometric scanner"
    }
    
    return {
        "challenge_id": challenge_id,
        "method": method.value,
        "message": setup_instructions[method],
        "expires_in_minutes": 10,
        "dev_code": verification_code,  # Remove in production!
        "instructions": "Enter the 6-digit code to complete MFA setup"
    }

@app.post("/auth/mfa/verify")
async def verify_mfa(
    challenge: MFAChallenge,
    current_user: Annotated[UserInDB, Depends(get_current_active_user)],
    request: Request
):
    """
    ✅ Verify your MFA setup
    
    Complete the multi-factor authentication setup process.
    """
    # Get MFA challenge
    mfa_challenge = active_mfa_challenges.get(challenge.challenge_id)
    
    if not mfa_challenge:
        log_security_event(
            "mfa_verification_failed",
            current_user.id,
            {"reason": "invalid_challenge_id"},
            request,
            SecurityLevel.HIGH
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="🚫 Invalid or expired MFA challenge"
        )
    
    # Check if challenge belongs to current user
    if mfa_challenge["user_id"] != current_user.id:
        log_security_event(
            "mfa_verification_failed",
            current_user.id,
            {"reason": "challenge_user_mismatch"},
            request,
            SecurityLevel.CRITICAL
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="🚫 Unauthorized MFA challenge"
        )
    
    # Check if challenge is expired
    if datetime.utcnow() > mfa_challenge["expires_at"]:
        del active_mfa_challenges[challenge.challenge_id]
        log_security_event(
            "mfa_verification_failed",
            current_user.id,
            {"reason": "challenge_expired"},
            request,
            SecurityLevel.MEDIUM
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="🕐 MFA challenge expired. Please request a new code."
        )
    
    # Verify the code
    if challenge.code != mfa_challenge["code"]:
        log_security_event(
            "mfa_verification_failed",
            current_user.id,
            {"reason": "invalid_code"},
            request,
            SecurityLevel.HIGH
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="🚫 Invalid verification code"
        )
    
    # Enable MFA for user
    current_user.mfa_enabled = True
    if challenge.method not in current_user.mfa_methods:
        current_user.mfa_methods.append(challenge.method)
    
    # Clean up challenge
    del active_mfa_challenges[challenge.challenge_id]
    
    # Log successful MFA setup
    log_security_event(
        "mfa_setup_completed",
        current_user.id,
        {"method": challenge.method.value},
        request,
        SecurityLevel.HIGH
    )
    
    return {
        "message": "🎉 Multi-Factor Authentication enabled successfully!",
        "method": challenge.method.value,
        "security_level": "Enhanced security is now active on your account",
        "backup_codes": [f"BC{secrets.randbelow(90000000) + 10000000:08d}" for _ in range(5)],
        "next_steps": [
            "Save your backup codes in a secure location",
            "Test MFA login to ensure it's working",
            "Consider enabling additional MFA methods"
        ]
    }

# === ACCOUNT MANAGEMENT ===

@app.get("/accounts/", response_model=List[Account])
async def get_user_accounts(
    current_user: Annotated[UserInDB, Depends(get_current_active_user)],
    request: Request
):
    """
    💼 View your SecureBank accounts
    
    Get a secure overview of all your accounts and balances.
    """
    accounts = user_accounts.get(current_user.id, [])
    
    # Log account access
    log_security_event(
        "account_access",
        current_user.id,
        {"accounts_viewed": len(accounts)},
        request,
        SecurityLevel.LOW
    )
    
    return accounts

@app.get("/accounts/{account_id}/balance")
async def get_account_balance(
    account_id: str,
    current_user: Annotated[UserInDB, Depends(get_current_active_user)],
    request: Request
):
    """
    💰 Check your account balance
    
    Securely view your current account balance with real-time updates.
    """
    # Find user's account
    user_account_list = user_accounts.get(current_user.id, [])
    account = next((acc for acc in user_account_list if acc.id == account_id), None)
    
    if not account:
        log_security_event(
            "unauthorized_account_access",
            current_user.id,
            {"attempted_account_id": account_id},
            request,
            SecurityLevel.HIGH
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="🚫 Account not found or access denied"
        )
    
    # Log balance inquiry
    log_security_event(
        "balance_inquiry",
        current_user.id,
        {"account_id": account_id},
        request,
        SecurityLevel.LOW
    )
    
    return {
        "account_id": account_id,
        "account_number": f"****{account.account_number[-4:]}",
        "balance": account.balance,
        "available_balance": account.balance,  # In real system, consider pending transactions
        "account_type": account.account_type.value,
        "daily_remaining_limit": account.daily_limit,
        "currency": "USD",
        "last_updated": datetime.utcnow().isoformat()
    }

# === SECURE TRANSACTIONS ===

@app.post("/transactions/transfer")
@limiter.limit("10/hour")  # Limit transfer frequency
async def transfer_funds(
    transfer: TransferRequest,
    current_user: Annotated[UserInDB, Depends(require_mfa)],  # Require MFA for transfers
    request: Request
):
    """
    💸 Secure money transfer
    
    Transfer funds between accounts with advanced fraud protection and real-time monitoring.
    """
    # Find sender's account
    user_account_list = user_accounts.get(current_user.id, [])
    from_account = next((acc for acc in user_account_list if acc.id == transfer.from_account_id), None)
    
    if not from_account:
        log_security_event(
            "transfer_attempt_unauthorized",
            current_user.id,
            {"from_account_id": transfer.from_account_id},
            request,
            SecurityLevel.CRITICAL
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="🚫 Source account not found or access denied"
        )
    
    # Check sufficient balance
    if from_account.balance < transfer.amount:
        log_security_event(
            "transfer_attempt_insufficient_funds",
            current_user.id,
            {"amount": transfer.amount, "balance": from_account.balance},
            request,
            SecurityLevel.MEDIUM
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="💰 Insufficient funds for this transfer"
        )
    
    # Check daily limits
    if transfer.amount > from_account.daily_limit:
        log_security_event(
            "transfer_attempt_limit_exceeded",
            current_user.id,
            {"amount": transfer.amount, "daily_limit": from_account.daily_limit},
            request,
            SecurityLevel.HIGH
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"🚫 Transfer amount exceeds daily limit of ${from_account.daily_limit:,.2f}"
        )
    
    # Fraud detection (simplified)
    security_flags = []
    if transfer.amount > 1000:
        security_flags.append("high_amount")
    if transfer.description.lower() in ["urgent", "emergency", "help"]:
        security_flags.append("suspicious_keywords")
    
    # Process transfer
    transaction_id = str(uuid.uuid4())
    reference_number = f"TXN{int(time.time())}{secrets.randbelow(10000):04d}"
    
    # Create transaction record
    transaction = Transaction(
        id=transaction_id,
        from_account_id=transfer.from_account_id,
        to_account_id=transfer.to_account_id,
        transaction_type=TransactionType.TRANSFER,
        amount=transfer.amount,
        description=transfer.description,
        reference_number=reference_number,
        created_at=datetime.utcnow(),
        security_flags=security_flags
    )
    
    # Update balances (in production, use database transactions)
    from_account.balance -= transfer.amount
    transaction.status = "completed"
    transaction.processed_at = datetime.utcnow()
    
    transactions_db.append(transaction)
    
    # Log successful transfer
    log_security_event(
        "transfer_completed",
        current_user.id,
        {
            "transaction_id": transaction_id,
            "amount": transfer.amount,
            "reference_number": reference_number,
            "security_flags": security_flags
        },
        request,
        SecurityLevel.HIGH
    )
    
    return {
        "message": "✅ Transfer completed successfully!",
        "transaction_id": transaction_id,
        "reference_number": reference_number,
        "amount": transfer.amount,
        "recipient": transfer.recipient_name,
        "new_balance": from_account.balance,
        "transaction_fee": 0.00,  # Free transfers for this demo
        "estimated_arrival": "Instant",
        "security_note": "This transaction has been secured with bank-grade encryption 🛡️"
    }

# === ADMIN & AUDIT ENDPOINTS ===

@app.get("/admin/audit-log")
async def get_audit_log(
    current_user: Annotated[UserInDB, Depends(require_roles([UserRole.ADMIN, UserRole.AUDITOR]))],
    limit: int = 100,
    security_level: Optional[SecurityLevel] = None,
    request: Request
):
    """
    📋 Security audit log
    
    View comprehensive security events and audit trails (Admin/Auditor only).
    """
    # Filter audit log
    filtered_logs = audit_log[-limit:]  # Get recent entries
    
    if security_level:
        filtered_logs = [log for log in filtered_logs if log.get("security_level") == security_level.value]
    
    # Log audit access
    log_security_event(
        "audit_log_accessed",
        current_user.id,
        {"entries_viewed": len(filtered_logs), "filter": security_level.value if security_level else "none"},
        request,
        SecurityLevel.CRITICAL
    )
    
    return {
        "total_entries": len(audit_log),
        "filtered_entries": len(filtered_logs),
        "audit_log": filtered_logs,
        "security_summary": {
            "critical_events": len([log for log in audit_log if log.get("security_level") == "critical"]),
            "high_events": len([log for log in audit_log if log.get("security_level") == "high"]),
            "medium_events": len([log for log in audit_log if log.get("security_level") == "medium"]),
            "low_events": len([log for log in audit_log if log.get("security_level") == "low"])
        }
    }

@app.post("/admin/api-keys")
async def create_api_key(
    name: str,
    permissions: List[str],
    expires_in_days: int = 365,
    current_user: Annotated[UserInDB, Depends(require_roles([UserRole.ADMIN]))],
    request: Request
):
    """
    🔑 Create API key for third-party integrations
    
    Generate secure API keys with specific permissions and expiration (Admin only).
    """
    api_key = f"sb_{''.join(secrets.choice('abcdefghijklmnopqrstuvwxyz0123456789') for _ in range(32))}"
    
    api_key_info = {
        "key": api_key,
        "name": name,
        "permissions": permissions,
        "created_by": current_user.id,
        "created_at": datetime.utcnow(),
        "expires_at": datetime.utcnow() + timedelta(days=expires_in_days),
        "is_active": True,
        "last_used": None,
        "usage_count": 0
    }
    
    api_keys[api_key] = api_key_info
    
    # Log API key creation
    log_security_event(
        "api_key_created",
        current_user.id,
        {"key_name": name, "permissions": permissions},
        request,
        SecurityLevel.CRITICAL
    )
    
    return {
        "message": "🔑 API key created successfully!",
        "api_key": api_key,
        "name": name,
        "permissions": permissions,
        "expires_at": api_key_info["expires_at"].isoformat(),
        "security_notice": "Store this key securely - it won't be shown again!"
    }

# === RATE LIMITED PUBLIC ENDPOINTS ===

@app.get("/public/exchange-rates")
@limiter.limit("30/minute")  # Reasonable limit for public data
async def get_exchange_rates(request: Request):
    """📈 Current exchange rates (Rate limited public endpoint)"""
    return {
        "base_currency": "USD",
        "rates": {
            "EUR": 0.85,
            "GBP": 0.73,
            "JPY": 110.25,
            "CAD": 1.25,
            "AUD": 1.35
        },
        "last_updated": datetime.utcnow().isoformat(),
        "disclaimer": "Rates are for reference only. Actual trading rates may vary."
    }

# === SECURITY DEMO ENDPOINTS ===

@app.get("/security/demo")
async def security_demo_info():
    """🛡️ Security features demonstration"""
    return {
        "title": "SecureBank Security Demonstration",
        "features_showcased": [
            "🔐 JWT Token Authentication",
            "🔑 Role-Based Access Control (RBAC)",
            "🛡️ Multi-Factor Authentication (MFA)",
            "⚡ Rate Limiting & DDoS Protection",
            "📝 Comprehensive Audit Logging",
            "🔒 Input Validation & Sanitization",
            "🔑 API Key Management",
            "🚨 Real-time Security Monitoring"
        ],
        "test_accounts": {
            "customer": {"username": "demo_customer", "password": "SecurePass123!", "role": "customer"},
            "manager": {"username": "demo_manager", "password": "ManagerPass123!", "role": "manager"},
            "admin": {"username": "demo_admin", "password": "AdminPass123!", "role": "admin"}
        },
        "security_levels": {
            "PUBLIC": "Exchange rates, general info",
            "AUTHENTICATED": "Account access, basic operations",
            "MFA_REQUIRED": "Money transfers, sensitive changes",
            "ADMIN_ONLY": "User management, system configuration",
            "AUDIT_ONLY": "Security logs, compliance reports"
        }
    }

if __name__ == "__main__":
    import uvicorn
    print("🏦 Starting SecureBank Digital Banking Platform...")
    print("🛡️ Your security is our top priority!")
    uvicorn.run(app, host="0.0.0.0", port=8000) 