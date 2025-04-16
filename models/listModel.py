from datetime import datetime
from typing import Any, List, Optional
from pydantic import BaseModel, Field, GetCoreSchemaHandler, GetJsonSchemaHandler
from bson import ObjectId
from pymongo import IndexModel, ASCENDING
import uuid
from pydantic_core import core_schema
from pydantic.json_schema import JsonSchemaValue

class PyObjectId(ObjectId):
    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: any, handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        return core_schema.with_info_after_validator_function(
            cls.validate,
            core_schema.union_schema([
                core_schema.str_schema(),
                core_schema.is_instance_schema(ObjectId)
            ]),
            serialization=core_schema.to_string_ser_schema(),
        )

    @classmethod
    def validate(cls, v: str | ObjectId, _: core_schema.ValidationInfo) -> ObjectId:
        print(f"Validating: {v} (type: {type(v)})")
        if isinstance(v, ObjectId):
            return v
        if ObjectId.is_valid(v):
            return ObjectId(v)
        raise ValueError("Invalid ObjectId")

    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema: dict) -> None:
        field_schema.update(type="string", example="507f1f77bcf86cd799439011")


    @classmethod
    def __get_pydantic_json_schema__(
        cls, 
        core_schema: Any, 
        handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        return handler(core_schema)


    @classmethod
    def __get_validators__(cls):
        yield cls.validate


class ListBase(BaseModel):
    """Shared attributes for all list operations"""
    name: str = Field(..., min_length=1, max_length=50, example="My Watchlist")


class ListDB(ListBase):
    """Complete model as stored in MongoDB"""
    # id: str = Field(default_factory=uuid.uuid4, alias="_id")
    owner_id: PyObjectId  # Reference to user
    items: List[str] = Field(default_factory=list)  # Tracked item IDs
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {ObjectId: str}
        allow_population_by_field_name = True
        schema_extra = {
            "example": {
                "_id": "507f1f77bcf86cd799439011",
                "owner_id": "507f191e810c19729de860ea",
                "name": "Prime Parts Checklist",
                "items": ["Nyx Prime Neuroptics", "Saryn Prime Chassis"],
                "created_at": "2023-01-01T00:00:00Z",
                "updated_at": "2023-01-02T12:00:00Z"
            }
        }

class ListCreate(ListBase):
    """Request model for creating new lists (name only)"""
    pass

class ListUpdate(BaseModel):
    """Request model for updating lists"""
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    add_items: Optional[List[str]] = None
    remove_items: Optional[List[str]] = None

class ListResponse(ListDB):
    """Response model with cleaned data"""
    id: PyObjectId = Field(alias="_id")
    # pass