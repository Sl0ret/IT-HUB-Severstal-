from abc import ABC, abstractmethod
from typing import List, Optional, Dict
from datetime import datetime
from ..models.schemas import RollStats, RollCreate, RollResponse

class StorageInterface(ABC):
    @abstractmethod
    def create_roll(self, roll: RollCreate) -> RollResponse:
        pass

    @abstractmethod
    def get_rolls(self, filters: Dict[str, Optional[str]]) -> List[RollResponse]:
        pass

    @abstractmethod
    def delete_roll(self, roll_id: int) -> Optional[RollResponse]:
        pass

    @abstractmethod
    def get_stats(self, start_date: datetime, end_date: datetime) -> RollStats:
        pass
