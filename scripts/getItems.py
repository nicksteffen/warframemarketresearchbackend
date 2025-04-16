import argparse
from pymongo import MongoClient
from dotenv import dotenv_values
import json
import requests
import statistics
from datetime import datetime, timedelta, timezone





config = dotenv_values("../.env")
TIME_FORMAT = "%Y-%m-%dT%H:%M:%S.00Z"


def write_dicts_to_log(dict_list, log_file="output.log", mode="a", format="json"):
    """
    Writes a list of dictionaries to a log file in a specified format.

    Args:
        dict_list (list): List of dictionaries to log.
        log_file (str): Path to the log file (default: "output.log").
        mode (str): File write mode - "a" (append) or "w" (overwrite) (default: "a").
        format (str): Output format - "json" or "pretty" (default: "json").
    """
    try:
        with open(f"{config["LOG_LOCATION"]}/{log_file}", mode) as f:
            timestamp = datetime.now().strftime("%Y-%m-%d-%H:%M:%S")
            f.write(f"\n\n=== Log Entry ({timestamp}) ===\n")
            
            for idx, entry in enumerate(dict_list, 1):
                f.write(f"\n--- Item {idx} ---\n")
                
                if format == "json":
                    json.dump(entry, f, indent=4, ensure_ascii=False)
                elif format == "pretty":
                    for key, value in entry.items():
                        f.write(f"{key}: {value}\n")
                else:
                    raise ValueError("Invalid format. Use 'json' or 'pretty'.")
                
                f.write("\n")  # Add spacing between entries
            
        print(f"Successfully logged {len(dict_list)} entries to {log_file}")
    except Exception as e:
        print(f"Error writing to log file: {e}")

def validate_item(item):
    if "id" in item.keys():
        del item["id"]
    if not item["wiki_link"]:
        item["wiki_link"] = ""
    return item


def add_item(data):
    """Adds the item to the database using an API endpoint with an updated last updated time"""
    data = validate_item(data)
    data["last_updated"] = datetime.now().strftime(TIME_FORMAT)
    resp = requests.post(f"{config['BACKEND_API']}:{config['BACKEND_API_PORT']}/item", json = data)
    return resp

def startup_db_client():
    mongodb_client = MongoClient(config["ATLAS_URI"])
    database = mongodb_client[config["DB_NAME"]]
    return database


def get_items_collection():
    return DB["items"]


def get_all_items():
    # returns the item url_names and their id in the database
    items = get_items_collection()
    # all_items = list(items.find({}, {"url_name" : 1}))
    all_items = list(items.find())
    return all_items

def get_items_from_web(limit_returned=None):
    # gets the list of items from warframe market
    print("Getting items list from web")
    items = requests.get("https://api.warframe.market/v1/items").json();
    return items["payload"]["items"][0:limit_returned]


def get_item_info_from_web(item = None, item_url = None):
    """ Get the item info from the web using the passed in item_url, or by getting the item_url from a passed in item"""
    if not item_url:
        if not item:
            raise Exception("no item or item_url provided")
        item_url = item["url_name"]
    raw_item_info = requests.get(f"https://api.warframe.market/v1/items/{item_url}").json()["payload"]["item"]["items_in_set"][0]
    item_info = {
        "thumb": raw_item_info["thumb"],
        "item_name": raw_item_info["en"]["item_name"],
        "wiki_link": raw_item_info["en"]["wiki_link"],
        "market_link": f"https://warframe.market/items/{item_url}",
        "rarity": raw_item_info.get("rarity", "N/A"),
        "tags": raw_item_info["tags"],
        "item_type": get_item_type(raw_item_info["tags"])
        }
    item.update(item_info)
    return item


def get_item_type(tags):
    if "mod" in tags:
        return "MOD"
    if "component" in tags:
        return "COMPONENT"
    return "OTHER"



def get_item_stat_from_web(item, mod_rank = 0):
    raw_item_order_info = requests.get(f"https://api.warframe.market/v1/items/{item['url_name']}/statistics").json()["payload"]["statistics_closed"]["48hours"]
    median = 0
    volume = 0
    if len(raw_item_order_info) > 0:
        if "mod_rank" in raw_item_order_info[0]:
            filtered_order_info = [order for order in raw_item_order_info if order["mod_rank"] == mod_rank]
        else:
            filtered_order_info = raw_item_order_info
        if filtered_order_info:
            median = statistics.mean([order["median"] for order in filtered_order_info])
            volume = statistics.mean([order["volume"] for order in filtered_order_info])
    item_order_info = {
            "median_price" : round(median, 2),
            "volume" : round(volume, 2),
            "rank" : mod_rank
    }
    item.update(item_order_info)
    return item


def add_new_items():
    # get list of items missing from items in db
    missing_items = getMissingItems()
    print(f"Found {len(missing_items)} missing items")
    log = []
    for item in missing_items:
        print("Updating missing items")
        log.append(createNewItem(item))
    # log of items created
    timestamp = datetime.now().strftime("%Y-%m-%d-%H:%M:%S")
    write_dicts_to_log(log, log_file=f"new_items_{timestamp}.log")


def getMissingItems():
    missing_items = []
    # get list of current items in db
    current_items = get_all_items()
    db_url_names = [item["url_name"] for item in current_items]
    # get list of all items from web
    web_items = get_items_from_web()
    missing_items = [web_item for web_item in web_items if web_item["url_name"] not in db_url_names]
    return missing_items

def createNewItem(item):
    #get item info
    item_info = get_item_info_from_web(item)
    #get item stats
    item_stats = get_item_stat_from_web(item_info)
    #add item to db using api
    resp = add_item(item_stats)
    # return request status -- todo make a report of items failed to add
    if resp.ok:
        return {"details": resp.json(),  "status": resp.status_code}
    else:
        return {"status": resp.status_code, "details":
                {"reason": resp.reason,
                 "item_name" : item_stats["item_name"]}}


def is_updated_within_one_day(item):
    last_updated = item.get("last_updated")
    now = datetime.now()
    # Calculate difference
    time_diff = now - last_updated
    return time_diff < timedelta(hours=24)

                
def get_expired(items):
    expired = [item for item in items if not is_updated_within_one_day(item)]
    return expired


def update_item_stats(item):
    item = get_item_stat_from_web(item)
    resp = update_item(item)
    if resp.ok:
        return {"details": resp.json(),  "status": resp.status_code}
    else:
        return {"status": resp.status_code, "details":
                {"reason": resp.reason,
                 "item_name" : item.get("item_name", item)}}


def update_item(item):
    resp = requests.put( f"{config['BACKEND_API']}:{config['BACKEND_API_PORT']}/item/{item["_id"]}", json=item)
    return resp    


def update_items():
    # should we populate the updated stat items to a queue and then update the db off the queue
    # to allow for faster updating? Or does it not matter since we'll do this like once a day for 3k items
    # if each update took 1second, then we'd take like 50 minutes to update all the items?
    items = get_all_items()
    expired_items = get_expired(items)[:10]
    print(f"Found {len(expired_items)} expired items to update")
    logs = []
    for item in expired_items:
        item["last_updated"] = datetime.now().strftime(TIME_FORMAT)
        update = update_item_stats(item)
        logs.append(update)
    timestamp = datetime.now().strftime("%Y-%m-%d-%H:%M:%S")
    write_dicts_to_log(logs, log_file=f"update_items_{timestamp}.log")




if __name__ == "__main__":
    DB = startup_db_client()


    parser = argparse.ArgumentParser(description="Manage your items")
    subparsers = parser.add_subparsers(dest='command', required=True, help='Available commands')

    # Add command for adding new items
    parser_add = subparsers.add_parser('add', help='Add new items')
    parser_add.set_defaults(func=add_new_items)

    # Add command for updating stats
    parser_update = subparsers.add_parser('update', help='Update item statistics')
    parser_update.set_defaults(func=update_items)

    # Parse arguments and call the appropriate function
    args = parser.parse_args()
    args.func()


