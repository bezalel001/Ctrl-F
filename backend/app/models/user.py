from pydantic import BaseModel, EmailStr


class UserProfile(BaseModel):
    id: str
    name: str
    email: EmailStr
    role: str
    department: str
    permissions: list[str]

