# from fastapi import Depends
# from pymongo.collection import Collection
# from main import app

# class DBCollections:
#     @staticmethod
#     def lists() -> Collection:
#         return app.database["lists"]
    
#     @staticmethod
#     def items() -> Collection:
#         return app.database["items"]
    
#     @staticmethod 
#     def users() -> Collection:
#         return app.database["users"]

# # lists_collection: Collection = Depends(DBCollections.lists)