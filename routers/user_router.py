import bcrypt

from fastapi import APIRouter, Body, Request, Response, HTTPException, status
from fastapi.encoders import jsonable_encoder
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from typing import List
from models.userModel import *

router = APIRouter()


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed_password.decode("utf-8")

# Verify password function
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))



@router.get("/")
def test():
    return "test"

# OAuth2 for token-based authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@router.post("/register", response_model=UserPublic)
async def register(user: UserCreate):
    # Check if the username or email already exists
    if users_collection.find_one({"username": user.username}):
        raise HTTPException(status_code=400, detail="Username already exists")
    if users_collection.find_one({"email": user.email}):
        raise HTTPException(status_code=400, detail="Email already exists")

    # Hash the password
    hashed_password = hash_password(user.password)

    # Create the user in the database
    user_data = UserInDB(
        **user.dict(),
        password_hash=hashed_password,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    ).dict()

    users_collection.insert_one(user_data)
    return user_data

@router.post("/login")
async def login(username: str, password: str):
    user = users_collection.find_one({"username": username})
    if not user or not verify_password(password, user["password_hash"]):
        raise HTTPException(status_code=400, detail="Invalid username or password")

    # Update last login time
    users_collection.update_one(
        {"username": username},
        {"$set": {"last_login": datetime.utcnow()}},
    )

    return {"message": "Login successful"}

@router.post("/watchlist/add", response_model=UserPublic)
async def add_to_watchlist(username: str, item_id: str):
    users_collection.update_one(
        {"username": username},
        {"$addToSet": {"watchlist": item_id}},  # Add item to watchlist if not already present
    )
    updated_user = users_collection.find_one({"username": username})
    return updated_user

@router.get("/watchlist", response_model=List[str])
async def get_watchlist(username: str):
    user = users_collection.find_one({"username": username})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user["watchlist"]