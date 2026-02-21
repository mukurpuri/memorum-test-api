from fastapi import APIRouter, HTTPException, Depends
from datetime import timedelta

from app.auth.models import LoginRequest, RegisterRequest, TokenResponse, AuthUser
from app.auth.jwt import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from app.auth.password import hash_password, verify_password
from app.auth.middleware import require_auth
from app.db.users import UserDB
from app.models import UserCreate

router = APIRouter()
db = UserDB()

passwords_store: dict = {}


@router.post("/register", response_model=TokenResponse)
async def register(request: RegisterRequest):
    existing = db.get_by_email(request.email.lower())
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")
    
    user_data = UserCreate(email=request.email.lower(), name=request.name)
    user = db.create(user_data)
    
    passwords_store[user.id] = hash_password(request.password)
    
    token = create_access_token(
        data={"sub": str(user.id), "email": user.email},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    return TokenResponse(
        access_token=token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    user = db.get_by_email(request.email.lower())
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    stored_hash = passwords_store.get(user.id)
    if not stored_hash or not verify_password(request.password, stored_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_access_token(
        data={"sub": str(user.id), "email": user.email},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    return TokenResponse(
        access_token=token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.get("/me", response_model=AuthUser)
async def get_current_user(payload: dict = Depends(require_auth)):
    user_id = int(payload.get("sub", 0))
    user = db.get_by_id(user_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return AuthUser(
        id=user.id,
        email=user.email,
        name=user.name,
        is_active=user.is_active
    )


@router.post("/logout")
async def logout(payload: dict = Depends(require_auth)):
    return {"message": "Successfully logged out"}
