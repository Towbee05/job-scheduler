from ninja import Schema
from pydantic import ConfigDict, field_validator
from datetime import datetime
from typing import List, Generic, TypeVar
from enum import Enum
import uuid


T = TypeVar("T")
SUCCESS_MESSAGE="success"
ERROR_MESSAGE="error"

class PriorityEnum(int, Enum):
    HIGH = 1
    MEDIUM = 2
    LOW = 3

class IntervalEnum(str, Enum):
    EVERY_1_MIN = "every_1_minute"
    EVERY_5_MIN = "every_5_minutes"
    EVERY_1_HR = "every_1_hour"

class CreateJob(Schema):
    type: str
    priority: PriorityEnum | None = PriorityEnum.LOW
    payload: dict
    scheduled_at: datetime | None = None
    interval: IntervalEnum| None = None
    dependencies: List[uuid.UUID] = []

class ListJob(Schema):
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    type: str
    priority: int
    mutated_priority: int
    payload: dict
    status: str
    scheduled_at: datetime
    retry_count: int
    processed_at: datetime | None = None
    interval: str | None = None
    created_at: datetime
    updated_at: datetime
    dependencies: List[uuid.UUID] = []

    @field_validator('dependencies', mode='before')
    @classmethod
    def resolve_dependencies(cls, v):
        if v is None:
            return []
        if hasattr(v, "values_list"):
            return list(v.values_list("id", flat=True))
        if isinstance(v, list):
            return [
                item.id if hasattr(item, "id") else item
                for item in v
            ]
        return v

class DLQ(Schema):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    job: ListJob
    error: str
    failed_at: datetime
    resolved: bool

class SuccessResponse(Schema, Generic[T]):
    status: str = SUCCESS_MESSAGE
    data: T

class ErrorResponse(Schema):
    status: str = ERROR_MESSAGE
    message: str
    error: str 

class MetaPaginatedResponse(Schema, Generic[T]):
    status: str = SUCCESS_MESSAGE
    total_pages: int
    current_page: int 
    limit: int
    data: T