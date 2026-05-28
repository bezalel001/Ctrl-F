from pydantic import BaseModel, EmailStr

from app.models.user import UserProfile


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserProfile

