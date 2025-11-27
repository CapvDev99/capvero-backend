from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from uuid import UUID

from src.models.user import UserRole


# Base schema
class UserBase(BaseModel):
    """Base user schema."""
    email: EmailStr
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    role: UserRole = UserRole.ENTREPRENEUR


# Schema for creating a user
class UserCreate(UserBase):
    """Schema for user creation."""
    password: str = Field(..., min_length=8, max_length=100)
    tenant_id: Optional[UUID] = None


# Schema for updating a user
class UserUpdate(BaseModel):
    """Schema for user update."""
    email: Optional[EmailStr] = None
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


# Schema for user in database
class UserInDB(UserBase):
    """Schema for user in database."""
    id: UUID
    is_active: bool
    is_verified: bool
    tenant_id: Optional[UUID]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Schema for user response
class UserResponse(UserInDB):
    """Schema for user response (without sensitive data)."""
    pass


# Schema for authentication
class Token(BaseModel):
    """Token response schema."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenPayload(BaseModel):
    """Token payload schema."""
    sub: str
    exp: int
    type: str
