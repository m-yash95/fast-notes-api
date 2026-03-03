from pydantic import BaseModel, EmailStr
from datetime import datetime

# Base schema containing common attributes
class UserBase(BaseModel):
    email: EmailStr  # Automatically validates proper email format

# Schema for creating a user (Input from the client)
class UserCreate(UserBase):
    password: str

# Schema for returning a user (Output to the client)
class UserResponse(UserBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True  # Allows Pydantic to read SQLAlchemy models

# --- TOKEN SCHEMAS ---
class Token(BaseModel):
    access_token: str
    token_type: str