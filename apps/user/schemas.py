from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: str | None = None
    disabled: bool | None = False


class UserCreate(UserBase):
    password: str


class UsersCreate(BaseModel):
    users: list[UserCreate]


class UserUpdate(BaseModel):
    username: str | None = None
    email: EmailStr | None = None
    full_name: str | None = None
    disabled: bool | None = None
    password: str | None = None


class User(UserBase):
    id: int


class UsersList(BaseModel):
    users: list[User]


class UserDeleteResponse(UserBase):
    id: int
    deleted: bool = True
