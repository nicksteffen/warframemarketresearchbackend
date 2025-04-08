from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr

class Filters(BaseModel):
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    rarity: Optional[List[str]] = None

class Notifications(BaseModel):
    email_alerts: bool = False
    price_drop_threshold: Optional[float] = None

class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str  # Plain-text password (will be hashed before storage)

# class UserLogin(UserBase):
    # password: str  # Plain-text password (will be hashed before storage
class UserLogin(BaseModel):
    email: EmailStr
    password: str  # Plain-text password (will be hashed before storage

class UserLoginResponse(BaseModel):
    access_token: str
    token_type: str

class UserInDB(UserBase):
    password_hash: str
    watchlist: List[str] = []
    filters: Optional[Filters] = None
    notifications: Optional[Notifications] = None
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None

class UserPublic(UserBase):
    watchlist: List[str]
    filters: Optional[Filters]
    notifications: Optional[Notifications]
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime]