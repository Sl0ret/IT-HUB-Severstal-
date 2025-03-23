# models.py
from sqlalchemy import Column, Integer, Float, DateTime
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()

class Roll(Base):
    __tablename__ = "rolls"

    id = Column(Integer, primary_key=True, autoincrement=True)
    length = Column(Float, nullable=False)
    weight = Column(Float, nullable=False)
    added_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    removed_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<Roll(id={self.id}, length={self.length}, weight={self.weight})>"

    def __str__(self):
        return self.__repr__()