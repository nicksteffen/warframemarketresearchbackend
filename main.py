from fastapi import FastAPI
from dotenv import dotenv_values
from pymongo import MongoClient



config = dotenv_values(".env")

app = FastAPI()

@app.on_event("startup")
def startup_db_client():
    app.mongodb_client = MongoClient(config["ATLAS_URI"])
    app.database = app.mongodb_client[config["DB_NAME"]]
    print("Connected to the MongoDB database!")

@app.on_event("shutdown")
def shutdown_db_client():
    app.mongodb_client.close()


def get_users_collection():
    return app.database["users"]

def get_items_collection():
    return app.database["items"]

def get_lists_collection():
    return app.database["lists"]

# note, importing after app is fully initialized to avoid circular dependency
from routers.item_router import router as item_router
from routers.user_router import router as user_router
from routers.lists_router import router as lists_router
app.include_router(item_router, tags=["items"], prefix="/item")
app.include_router(user_router, tags=["users"], prefix="/user")
app.include_router(lists_router, tags=["lists"], prefix="/lists")