import re
from fastapi import HTTPException


EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
NAME_MIN_LENGTH = 2
NAME_MAX_LENGTH = 100


def validate_email(email: str) -> str:
    email = email.strip().lower()
    if not EMAIL_REGEX.match(email):
        raise HTTPException(status_code=400, detail="Invalid email format")
    return email


def validate_name(name: str) -> str:
    name = name.strip()
    if len(name) < NAME_MIN_LENGTH:
        raise HTTPException(status_code=400, detail=f"Name must be at least {NAME_MIN_LENGTH} characters")
    if len(name) > NAME_MAX_LENGTH:
        raise HTTPException(status_code=400, detail=f"Name must be at most {NAME_MAX_LENGTH} characters")
    return name
