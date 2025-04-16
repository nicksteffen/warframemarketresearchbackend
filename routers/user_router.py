from datetime import timedelta
from dotenv import dotenv_values
from fastapi import APIRouter, Body, Request, Response, HTTPException, status
from fastapi.encoders import jsonable_encoder
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from typing import List
from models.itemModels import Item
from models.userModel import *
from jose import jwt, JWTError
import bcrypt


router = APIRouter()


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed_password.decode("utf-8")

# Verify password function
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))



# OAuth2 for token-based authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


config = dotenv_values(".env")

SECRET_KEY = config.get("TOKEN_KEY")
ALGORITHM = config.get("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(config.get("ACCESS_TOKEN_EXPIRE_MINUTES"))

credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
async def get_current_user_email(token: str = Depends(oauth2_scheme),):
    print("here's the token")
    print(token)
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    return email



@router.get("/protected")
async def protected_route(request: Request, 
                          current_user: dict = Depends(get_current_user_email)):

    print("HIT PROTEC")
    users_collection = request.app.database["users"]
    user = users_collection.find_one({"email": current_user})
    if user is None:
        raise credentials_exception
    # return user
    return {"message": "You are authenticated", "user": user["username"]}

def create_access_token(data: dict):
    # Create a JWT token with the user information and expiration time
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
    # return user

@router.post("/register", response_description="Create a new user with a unique username and email, or return an error if already exists", response_model=UserPublic)
async def register(request: Request, user: UserCreate):
    print("HIT REGISTER")
    # Check if the username or email already exists
    users_collection = request.app.database["users"]
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

@router.post("/login", response_model=UserLoginResponse)
async def login(request: Request, user: UserLogin):
                # username: str, password: str):
    print("HIT LOGIN")
    users_collection = request.app.database["users"]
    # db_user = users_collection.find_one({"username": user.username})
    db_user = users_collection.find_one({"email": user.email})
    if not db_user or not verify_password(user.password, db_user["password_hash"]):
        raise HTTPException(status_code=400, detail="Invalid username or password")

    # Update last login time
    users_collection.update_one(
        # {"username": user.username},
        {"email": user.email},
        {"$set": {"last_login": datetime.utcnow()}},
    )
    # Create JWT token
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}


# todo, these should depend on the token  and pull the username that way
# todo - This probably isn't a proper POST request, we're updating part of 
# the watchlist. Actually, this logic maybe needs to completely move to the new
# lists router
@router.post("/watchlist/delete", response_model=UserPublic)
async def delete_from_user_list(request: Request, body: dict = Body(...),
                                current_user: dict = Depends(get_current_user_email)):
    users_collection = request.app.database["users"]

    data = jsonable_encoder(body)
    print("delete items")
    print(body)
    # userId = data.get("userId")
    user_email = current_user
    itemIds = data.get("itemIds")
    # print(itemIds)

    users_collection.update_one(
        {'email': user_email},
        {"$pull": {"watchlist": {"$in" : itemIds} }}
    )
    updated_user = users_collection.find_one({"email": user_email})
    return updated_user

# todo - made redundant by lists router
@router.post("/watchlist/add", response_model=UserPublic)
async def add_to_user_list(request: Request, body: dict = Body(...),
                           current_user: dict = Depends(get_current_user_email)):
    users_collection = request.app.database["users"]

    data = jsonable_encoder(body)
    print("USERID:")
    print(data.get("userId"))
    print("ITEM ID: ")
    print(data.get("itemId"))
    print(current_user)
    user_email = current_user
    userId = data.get("userId")
    itemIds = data.get("itemIds")
    users_collection.update_one(
        {'email': user_email},
        # {"username": userId},
        {"$addToSet": {"watchlist":  {
                       "$each": itemIds}}},  # Add item to watchlist if not already present
    )
    # updated_user = users_collection.find_one({"username": userId})
    updated_user = users_collection.find_one({"email": user_email})
    return updated_user

# todo, maybe it makes sense that this should just return the list of ids, and then we can have a separate call to return a list of items
# we could then make things like mod and primes also just return ids, and then have a single call for returning items in a list
# todo - made redundant by lists router
@router.get("/watchlist", response_model=List[Item])
async def get_watchlist(request: Request, current_user: dict = Depends(get_current_user_email)):
    print("get watchlist")
    users_collection = request.app.database["users"]
    # print(username)
    # username = 
    user = users_collection.find_one({"email": current_user})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    print(user)
    item_ids = user["watchlist"]
    items = list(request.app.database["items"].find({"_id": { "$in" : item_ids } } ) )
    print(items)
    return items

   