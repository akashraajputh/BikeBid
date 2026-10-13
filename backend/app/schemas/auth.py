from pydantic import BaseModel, EmailStr, Field


class UserRegister(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=80)
    full_name: str = Field(min_length=1, max_length=150)
    password: str = Field(min_length=8, max_length=128)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserPublic(BaseModel):
    id: int
    email: str
    username: str
    full_name: str
    role: str
    is_active: bool = True


class AuthResponse(BaseModel):
    token: str
    refresh_token: str
    user: UserPublic


class RefreshRequest(BaseModel):
    refresh_token: str
