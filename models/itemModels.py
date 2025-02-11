import uuid
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime



class Item(BaseModel):
    id: str = Field(default_factory=uuid.uuid4, alias="_id")
    url_name: str = Field(...)
    thumb: str = Field(...)
    item_name: str = Field(...)
    rank: int = Field(...)
    wiki_link: str = Field(...)
    market_link: str = Field(...)
    median_price: float = Field(...)
    volume: float = Field(...)
    last_updated: datetime = Field(...)
    rarity: str = Field(...)
    tags: List[str] = Field(...)
    item_type: str = Field(...) # MOD or COMPONENT

    class Config:
        allow_population_by_field_name = True
        schema_extra = {
            "example": {
                
                "thumb": "https://example.com/image.jpg",
                "item_name": "Example Item",
                "rank": 5,
                "wiki_link": "https://example.com/wiki/example-item",
                "market_link": "https://example.com/wiki/example-item",
                "median_price": 12.99,
                "volume": 150.75,
                "last_updated": "2025-01-30T12:34:56Z",
                "rarity": "common",
                "tags": ["melee", "mod", "rare"],
                "item_type": "MOD",
            }
        }


class ItemUpdate(BaseModel):
    url_name: Optional[str] = None
    thumb: Optional[str] = None
    item_name: Optional[str] = None
    rank: Optional[int] = None
    wiki_link: Optional[str] = None
    market_link: Optional[str] = None
    median_price: Optional[float] = None
    volume: Optional[float] = None
    last_updated: Optional[datetime] = None
    rarity: Optional[str] = None
    tags: Optional[List[str]] = None 
    item_type: Optional[str] = None

    class Config:
        allow_population_by_field_name = True
        schema_extra = {
            "example": {
                "url_name": "example-item",
                "thumb": "https://example.com/image.jpg",
                "item_name": "Example Item",
                "rank": 5,
                "wiki_link": "https://example.com/wiki/example-item",
                "market_link": "https://example.com/wiki/example-item",
                "median_price": 12.99,
                "volume": 150.75,
                "last_updated": "2025-01-30T12:34:56Z",
                "rarity": "common",
                "tags": ["melee", "mod", "rare"],
                "item_type": "MOD"
            }
        }

