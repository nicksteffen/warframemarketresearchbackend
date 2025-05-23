from fastapi import APIRouter, Body, Request, Response, HTTPException, status
from fastapi.encoders import jsonable_encoder
from typing import List

from models.itemModels import Item, ItemUpdate, Filter

router = APIRouter()



@router.post("/", response_description="Create a new item", status_code=status.HTTP_201_CREATED, response_model=Item)
def create_item(request: Request, item: Item = Body(...)):
    item = jsonable_encoder(item)
    new_item = request.app.database["items"].insert_one(item)
    created_item = request.app.database["items"].find_one(
        {"_id": new_item.inserted_id}
    )

    return created_item

# todo see todo in the user_router about getting items by id instead
@router.get("/mods", response_description="List all items with item_type MOD", response_model=List[Item])
def list_mods(request: Request):
    items = list(request.app.database["items"].find({"item_type": "MOD"}))
    return items

@router.get("/primes", response_description="List all prime parts items", response_model=List[Item])
def list_prime_parts(request: Request):
    items = list(request.app.database["items"].find({"item_type": "COMPONENT"}))
    return items

@router.get("/arcanes", response_description="List all arcaneitems", response_model=List[Item])
def list_arcanes(request: Request):
    items = list(request.app.database["items"].find({"item_type": "ARCANE"}))
    return items

#todo mods and primes need to be one method, and we pass in the filter somehow
#  thoughts: we just pass in the filter as an object. e.g. {filter: {"item_type": "COMPONENT"}}
@router.post("/search-items", response_description="Return all items mathcing the filter clause", response_model=List[Item])
# def get_items_by_filter(request: Request, body: dict = Body(...)):
def get_items_by_filter(request: Request, body: Filter): 
    data = jsonable_encoder(body)
    property_name = data["property_name"]
    search_term = data["search_term"]
    filter = {property_name : search_term}
    wildcard = data["wildcard"]
    if wildcard:
        filter = {property_name: 
                   {"$regex" : search_term}}

    print(f"data filter = {filter}")
    items = list(request.app.database["items"].find(filter))

    return items

#todo I think think is no longer used/ was just used for test
@router.get("/my-list/{user_id}", response_description="List all items in the users list of items tracked", response_model=List[Item])
def list_user_items(user_id: str, request: Request):
    print("my-list")

    item_ids = [
        "b0029414-5c7e-4eca-8bea-a629c3d2d02a",
        "797b32b2-8cb3-48d2-a6e4-5ce492d0082e",
        "3e939338-60dd-4784-bc2a-ca5d81ec134a",
    ]


    items = list(request.app.database["items"].find({"_id": { "$in" : item_ids } } ) )
    return items



@router.post("/user-action/add-to-list", response_description="Try to add an item to the user's list", response_model=List[Item])
def add_to_user_list(request: Request, body: dict = Body(...)):
    print("got data")
    data = jsonable_encoder(body)
    print(data)
    user_id = data["userId"]
    item = data["item"]
    print(user_id)
    print(item["item_name"])
    
    # print(body.keys())



    return [item]


@router.get("/", response_description="List all items", response_model=List[Item])
def list_items(request: Request):
    items = list(request.app.database["items"].find())
    return items

@router.get("/{id}", response_description="Get a single item by id", response_model=Item)
def find_item(id: str, request: Request):
    if (item := request.app.database["items"].find_one({"_id": id})) is not None:
        return item
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Item with ID {id} not found")

@router.post("/get-items", response_description="Get multiple items by IDs", response_model=List[Item])
def find_items(request: Request, ids: List[str] = Body(...)):
    # Query MongoDB for items matching any of the provided IDs
    items = list(request.app.database["items"].find({"_id": {"$in": ids}}))
    
    if not items:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No items found with the provided IDs"
        )
    
    print(f"found itesm: {items}")
    return items

@router.put("/{id}", response_description="Update a item", response_model=Item)
def update_item(id: str, request: Request, item: ItemUpdate = Body(...)):
    item = {k: v for k, v in item.dict().items() if v is not None}
    if len(item) >= 1:
        update_result = request.app.database["items"].update_one(
            {"_id": id}, {"$set": item}
        )

        if update_result.modified_count == 0:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Item with ID {id} not found")

    if (
        existing_item := request.app.database["items"].find_one({"_id": id})
    ) is not None:
        return existing_item

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Item with ID {id} not found")



@router.delete("/{id}", response_description="Delete a item")
def delete_item(id: str, request: Request, response: Response):
    delete_result = request.app.database["items"].delete_one({"_id": id})

    if delete_result.deleted_count == 1:
        response.status_code = status.HTTP_204_NO_CONTENT
        return response

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Item with ID {id} not found")