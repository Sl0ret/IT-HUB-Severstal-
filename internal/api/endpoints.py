from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
from typing import Optional
from ..logger.logger import logger
from ..models import schemas
from ..storage.database import get_storage
from ..storage.storage import StorageInterface

router = APIRouter()

@router.post("/rolls/", response_model=schemas.RollResponse)
async def create_roll(
    roll: schemas.RollCreate,
    storage: StorageInterface = Depends(get_storage)
):
    logger.info("Creating roll", extra={"data": roll.model_dump()})
    try:
        result = storage.create_roll(roll)
        logger.debug("Roll created", extra={"roll_id": result.id})
        return result
    except Exception as e:
        logger.error("Roll creation failed", exc_info=True)
        raise HTTPException(500, "Creation error")

@router.get("/rolls/", response_model=list[schemas.RollResponse])
async def get_rolls(
    id_range: Optional[str] = None,
    weight_range: Optional[str] = None,
    length_range: Optional[str] = None,
    added_at_range: Optional[str] = None,
    removed_at_range: Optional[str] = None,
    storage: StorageInterface = Depends(get_storage)
):
    filters = {k: v for k, v in locals().items() if k != "storage"}
    logger.info("Fetching rolls", extra={"filters": filters})

    try:
        result = storage.get_rolls(filters)
        logger.debug(f"Found {len(result)} rolls")
        return result
    except ValueError as e:
        logger.warning("Invalid filter format", extra={"error": str(e)})
        raise HTTPException(400, "Invalid filter format")
    except Exception as e:
        logger.error("Fetch error", exc_info=True)
        raise HTTPException(500, "Fetch error")

@router.delete("/rolls/{roll_id}", response_model=schemas.RollResponse)
async def delete_roll(
    roll_id: int,
    storage: StorageInterface = Depends(get_storage)
):
    logger.info(f"Deleting roll {roll_id}")
    try:
        result = storage.delete_roll(roll_id)
        if not result:
            logger.warning("Roll not found", extra={"roll_id": roll_id})
            raise HTTPException(404, "Roll not found")
        logger.debug("Roll deleted", extra={"roll_id": roll_id})
        return result
    except Exception as e:
        logger.error("Deletion failed", exc_info=True)
        raise HTTPException(500, "Deletion error")

@router.get("/rolls/stats/", response_model=schemas.RollStats)
async def get_stats(
    start_date: datetime,
    end_date: datetime,
    storage: StorageInterface = Depends(get_storage)
):
    logger.info("Calculating stats", extra={
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat()
    })
    try:
        return storage.get_stats(start_date, end_date)
    except Exception as e:
        logger.error("Stats calculation failed", exc_info=True)
        raise HTTPException(500, "Stats error")