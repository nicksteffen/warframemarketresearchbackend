from fastapi import APIRouter, Body, Request, Response, HTTPException, status
from fastapi.encoders import jsonable_encoder
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from typing import List
from models.itemModels import Item
from models.userModel import *
import bcrypt


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

@router.post("/register", response_description="Create a new user with a unique username and email, or return an error if already exists", response_model=UserPublic)
async def register(request: Request, user: UserCreate):
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

@router.post("/login")
async def login(request: Request, username: str, password: str):
    users_collection = request.app.database["users"]
    user = users_collection.find_one({"username": username})
    if not user or not verify_password(password, user["password_hash"]):
        raise HTTPException(status_code=400, detail="Invalid username or password")

    # Update last login time
    users_collection.update_one(
        {"username": username},
        {"$set": {"last_login": datetime.utcnow()}},
    )

    return {"message": "Login successful"}

@router.post("/watchlist/delete", response_model=UserPublic)
async def delete_from_user_list(request: Request, body: dict = Body(...)):
    users_collection = request.app.database["users"]

    data = jsonable_encoder(body)
    print("delete items")
    print(body)
    userId = data.get("userId")
    itemIds = data.get("itemIds")
    print(itemIds)

    users_collection.update_one(
        {"username": userId},
        {"$pull": {"watchlist": {"$in" : itemIds} }}
    )
    updated_user = users_collection.find_one({"username": userId})
    return updated_user




@router.post("/watchlist/add", response_model=UserPublic)
async def add_to_user_list(request: Request, body: dict = Body(...)):
    users_collection = request.app.database["users"]

    data = jsonable_encoder(body)
    print(data.get("userId"))
    print(data.get("itemId"))
    userId = data.get("userId")
    itemId = data.get("itemId")
    users_collection.update_one(
        {"username": userId},
        {"$addToSet": {"watchlist": itemId}},  # Add item to watchlist if not already present
    )
    updated_user = users_collection.find_one({"username": userId})
    return updated_user

    # test_user = UserPublic(
    # id="test123",  # Assuming id comes from UserBase
    # email="test@example.com", # Assuming email comes from UserBase
    # username="testuser", # Assuming username comes from UserBase
    # watchlist=[],
    # watchlist=["BTC", "ETH", "SOL"],
    # filters=Filters(
        # min_price=10.00,
        # max_price=100.0,
        # rarity=[]
    # ),
    # notifications=Notifications(
        # email_alerts=True,
        # price_drop_threshold=0.0
    # ),
    # created_at=datetime.now(),
    # updated_at=datetime.now(),
    # last_login=datetime.now()
    # )

    # return test_user

# todo, maybe it makes sense that this should just return the list of ids, and then we can have a separate call to return a list of items
# we could then make things like mod and primes also just return ids, and then have a single call for returning items in a list
@router.get("/watchlist", response_model=List[Item])
async def get_watchlist(request: Request, username: str):
    users_collection = request.app.database["users"]
    print(username)
    # username = 
    user = users_collection.find_one({"username": username})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    

    # return user["watchlist"]


    # item_ids = [
        # "b0029414-5c7e-4eca-8bea-a629c3d2d02a",
        # "797b32b2-8cb3-48d2-a6e4-5ce492d0082e",
        # "3e939338-60dd-4784-bc2a-ca5d81ec134a",
    # ]


    item_ids = user["watchlist"]
    items = list(request.app.database["items"].find({"_id": { "$in" : item_ids } } ) )
    print(items)
    return items