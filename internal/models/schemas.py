from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class RollCreate(BaseModel):
    length: float
    weight: float

class RollResponse(BaseModel):
    id: int
    length: float
    weight: float
    added_at: datetime
    removed_at: Optional[datetime]


class RollFilter(BaseModel):
    id_range: Optional[str] = None
    weight_range: Optional[str] = None
    length_range: Optional[str] = None
    added_at_range: Optional[str] = None
    removed_at_range: Optional[str] = None

class RollStats(BaseModel):
    total_added: int
    total_removed: int
    avg_length: float
    avg_weight: float
    max_length: float
    min_length: float
    max_weight: float
    min_weight: float
    total_weight: float
    max_time_diff: Optional[float]
    min_time_diff: Optional[float]

