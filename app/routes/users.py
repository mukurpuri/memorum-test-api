from fastapi import APIRouter, HTTPException
from typing import List
from datetime import datetime

from app.models import User, UserCreate, UserResponse
from app.db.users import UserDB

router = APIRouter()
db = UserDB()


@router.get("/", response_model=List[User])
async def list_users():
    return db.get_all()


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int):
    user = db.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse(success=True, data=user)


@router.post("/", response_model=UserResponse)
async def create_user(user: UserCreate):
    new_user = db.create(user)
    return UserResponse(success=True, data=new_user)
