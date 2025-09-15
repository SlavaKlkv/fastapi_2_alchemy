from datetime import datetime
from typing import TypedDict

from pydantic import EmailStr

from apps.user.schemas import User, UserCreate


class UserRecord(TypedDict):
    id: int
    username: str
    email: EmailStr
    full_name: str | None
    disabled: bool
    hashed_password: str
    created_at: float
    updated_at: float


def to_record(new_id: int, payload: UserCreate, pwd_hash: str) -> UserRecord:
    now = datetime.now().timestamp()
    return UserRecord(
        id=new_id,
        username=payload.username,
        email=payload.email,
        full_name=payload.full_name,
        disabled=False,
        hashed_password=pwd_hash,
        created_at=now,
        updated_at=now,
    )


def to_public(rec: UserRecord) -> User:
    return User(
        id=rec['id'],
        username=rec['username'],
        email=rec['email'],
        full_name=rec['full_name'],
        disabled=rec['disabled'],
    )
