from typing import List, Optional
from datetime import datetime

from app.models import User, UserCreate


class UserDB:
    """In-memory user storage for demo purposes."""
    
    def __init__(self):
        self._users: List[User] = []
        self._next_id = 1
    
    def get_all(self) -> List[User]:
        return self._users
    
    def get_by_id(self, user_id: int) -> Optional[User]:
        for user in self._users:
            if user.id == user_id:
                return user
        return None
    
    def get_by_email(self, email: str) -> Optional[User]:
        for user in self._users:
            if user.email == email:
                return user
        return None
    
    def create(self, user_data: UserCreate) -> User:
        user = User(
            id=self._next_id,
            email=user_data.email,
            name=user_data.name,
            created_at=datetime.utcnow(),
            is_active=True
        )
        self._users.append(user)
        self._next_id += 1
        return user
