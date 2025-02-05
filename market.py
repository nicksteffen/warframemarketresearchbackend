import json
import requests
import statistics
import datetime

from bson import json_util



ITEMS_FILE = "items.json"
ITEM_INFO_FILE = "item_info.json"
ITEM_STATS_FILE = "item_stats.json"
TIME_FORMAT = "%Y-%m-%dT%H:%M:%S.00Z"

class ItemFileException(Exception):
    pass

def add_item(data):
    data["last_updated"] = datetime.datetime.now().strftime(TIME_FORMAT)
    print(data)
    resp = requests.post("http://localhost:8000/item/", json = data)
                        #  json.dumps(data))
                        #  , default = json_util.default))
    # print(resp)
    return resp

def get_item_type(tags):
    if "mod" in tags:
        return "MOD"
    if "component" in tags:
        return "COMPONENT"
    return "OTHER"

def write_to_file(data, file):
    print(f"Writing items to file {file}")
    with open (file, 'w') as f:
        json.dump(data, f)

def get_from_file(file):
    try:
        with open(file, 'r') as f:
            items = json.load(f)
        return items
    except Exception as e:
        raise ItemFileException(f"Could not open file: {file}")


def get_items_from_web(limit_returned=None):
    print("Getting items list from web")
    items = requests.get("https://api.warframe.market/v1/items").json();
    return items["payload"]["items"][0:limit_returned]

def get_items_from_file(file = ITEMS_FILE, limit=None):
    items = get_from_file(file)[0:limit]
    return items

def get_items(limit=None, file = ITEMS_FILE):
    """Attempts to get the items list from file, then pulls them from the web and writes the file if there's an error"""
    try: 
        items = get_items_from_file(file, limit)
    except ItemFileException as e:
        print(f"There was an issue reading from the items file: {e}.")
        items = get_items_from_web(limit)
        write_to_file(items, file)
    return items

def get_items_info_from_web(items):
    return [get_item_info_from_web(item) for item in items]


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


def get_items_info_from_file(file = ITEM_INFO_FILE):
    items_info = get_from_file(file)
    return items_info


def get_items_info(items, file = ITEM_INFO_FILE):
    """Attempt to read items info from file, if not update the items list passed in. NOTE: this will overwrite any existing data"""
    try:
        items_info = get_items_info_from_file()
    except ItemFileException as e:
        print(f"There was an issue read from the item info file: {e}")
        items_info = get_items_info_from_web(items)
        write_to_file(items_info, file)
    return items_info

def get_item_stats_from_web(items):
    return [get_item_stat_from_web(item) for item in items]

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


def get_item_stats_from_file(file = ITEM_STATS_FILE):
    return get_from_file(file)

def get_item_stats(items, file = ITEM_STATS_FILE):
    """Attempt to read items stats from file, if not update the items list passed in. NOTE: this will overwrite any existing data"""
    try:
        item_stats = get_item_stats_from_file(file)
    except ItemFileException as e:
        print(f"There was an issue reading the item stats from file: {e}")
        item_stats = get_item_stats_from_web(items)
        write_to_file(item_stats, file)
    return item_stats


# todo implement some filtering to just get mods or prime parts etc
def get_all_item_objects(limit = None, item_file = ITEMS_FILE, items_info_file = ITEM_INFO_FILE, items_stats_file = ITEM_STATS_FILE):
    print("TOP: getting items")
    items = get_items(limit, item_file)
    print("TOP: getting items info")
    items_info = get_items_info(items, items_info_file)
    print("TOP: getting items stats")
    items_stats = get_item_stats(items_info, items_stats_file)
    # return items
    # return items_info
    return items_stats



if __name__ == "__main__":
    test_item = {
        "url_name": "wisp_prime_blueprint",
        "thumb": "https://example.com/image.jpg",
        "item_name": "Wisp Prime Blueprint",
        "rank": 0,
        "wiki_link": "https://example.com/wiki/example-item",
        "market_link": "https://example.com/wiki/example-item",
        "median_price": 2.99,
        "volume": 10.75,
        "last_updated": "2025-01-30T12:34:56Z",
        "rarity": "common",
        "tags": ["mod", "common", "warframe"],
        "item_type": "COMPONENT"
    }
    # print(get_all_item_objects(100))
    # print(get_all_item_objects())
    # print(len(get_all_item_objects()))
    objs = get_all_item_objects()
    # print(objs[0:10])
    responses = [add_item(data) for data in objs]
    print(responses)
    # items = get_items()
    # items_info = get_items_info(items)
    # print(len(items_info))
    # print(len(objs))
    



    