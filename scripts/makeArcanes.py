import argparse
from pymongo import MongoClient
from dotenv import dotenv_values
import json
import requests
import statistics
from datetime import datetime, timedelta, timezone





config = dotenv_values("../.env")
TIME_FORMAT = "%Y-%m-%dT%H:%M:%S.00Z"



def startup_db_client():
    mongodb_client = MongoClient(config["ATLAS_URI"])
    database = mongodb_client[config["DB_NAME"]]
    return database


def get_items_collection(db):
    return db["items"]
    


def get_arcanes_by_tag(db):
    items = get_items_collection(db)
    arcanes = list(items.find({"tags": {"$in": ["arcane_enhancement"]}}))
    return arcanes

def transform_arcanes(db):
    collection = get_items_collection(db)
    update_operation = {"$set": {"item_type": "ARCANE"}}
    filter_query = {"tags": {"$in": ["arcane_enhancement"]}}
    collection.update_many(filter_query, update_operation)
    

