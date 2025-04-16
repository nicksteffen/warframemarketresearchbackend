from datetime import datetime
from typing import List
from fastapi import APIRouter, Body, Depends, HTTPException, Request, status
from fastapi.encoders import jsonable_encoder
# from dependencies import DBCollections
from models.listModel import ListCreate, ListDB, ListUpdate, ListResponse, PyObjectId
from core.auth import auth_service
from pymongo.collection import Collection
from main import get_lists_collection

router = APIRouter()

@router.post("/", response_model=ListResponse, status_code=status.HTTP_201_CREATED)
async def create_list(
    list_data: ListCreate,
    current_user: PyObjectId = Depends(auth_service.get_current_user_id),
    lists_collection : Collection = Depends(get_lists_collection)
):
    """Create a new tracking list (only requires name)"""
    list_name = dict(list_data).get("name")
    print(current_user)
    db_list = ListDB(
        # **dict(list_data),
        name= list_name,
        owner_id=current_user,
        items=[],
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
        # item = jsonable_encoder(item)
    jsonable = jsonable_encoder(db_list)
    print(db_list)
    result = lists_collection.insert_one(dict(db_list))
    # result = lists_collection.insert_one(jsonable)
    created_list = lists_collection.find_one({"_id": result.inserted_id})
    
    return ListResponse(**created_list)

@router.get("/", response_model=List[ListResponse])
async def get_user_lists(current_user: PyObjectId = Depends(auth_service.get_current_user_id),
                         lists_collection : Collection = Depends(get_lists_collection)):
    """Get all lists for the current user"""
    print(f"Gettting user lists for current user with id {current_user}")
    # test = [t for t in lists_collection.find()]
    # print(type(test[-1]["owner_id"]))
    # print(type(current_user))
    user_lists = lists_collection.find({"owner_id": current_user})
    print(f"user_lists: {user_lists}")
    # print([lst for lst in user_lists])
    # print([ListResponse(**lst) for lst in user_lists])
    # print("=====")
    return [ListResponse(**lst) for lst in user_lists]

@router.get("/{list_id}", response_model=ListResponse)
async def get_list(
    list_id: PyObjectId,
    current_user: PyObjectId = Depends(auth_service.get_current_user_id),
    lists_collection : Collection = Depends(get_lists_collection)):
    """Get a specific list by ID"""
    if (lst := lists_collection.find_one({"_id": list_id, "owner_id": current_user})) is None:
        raise HTTPException(status_code=404, detail="List not found")
    return ListResponse(**lst)

# todo: do we want to use PATCH here? It's probably technically correct, but does that make it right?
@router.post("/{list_id}", response_model=ListResponse)
async def update_list(
    list_id: PyObjectId,
    update_data: ListUpdate,
    current_user: PyObjectId = Depends(auth_service.get_current_user_id),
    lists_collection : Collection = Depends(get_lists_collection)):
    """Update list name or modify items"""
    existing = lists_collection.find_one({"_id": list_id, "owner_id": current_user})
    if not existing:
        raise HTTPException(status_code=404, detail="List not found")
    updates = {
        "$set": {"updated_at": datetime.utcnow()}
    }
    
    # Update name if provided
    if update_data.name:
        updates["$set"]["name"] = update_data.name
    
    if update_data.add_items:
        items_to_add = update_data.add_items if isinstance(update_data.add_items, list) else [update_data.add_items]
        updates["$addToSet"] = {
            "items": {
                "$each": items_to_add
            }
        }
    
    # Remove items if provided
    if update_data.remove_items:
        updates["$pullAll"] = {
            "items": update_data.remove_items if isinstance(update_data.remove_items, list) else [update_data.remove_items]
        }
    
    # Perform the update
    result = lists_collection.update_one(
        {"_id": list_id, "owner_id": current_user},
        updates
    )

     
    updated_list = lists_collection.find_one({"_id": list_id})
    return ListResponse(**updated_list)

@router.delete("/{list_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_list(
    list_id: PyObjectId,
    current_user: PyObjectId = Depends(auth_service.get_current_user_id),
    lists_collection : Collection = Depends(get_lists_collection)):
    """Delete a list"""
    result = lists_collection.delete_one({"_id": list_id, "owner_id": current_user})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="List not found")
    return None
