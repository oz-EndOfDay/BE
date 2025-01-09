import re
from datetime import datetime
from typing import Type, TypeVar

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer

from src.config.database.orm import Base

T = TypeVar("T", bound="Friend")  # Generic type variable for the class method


class Friend(Base):
    __tablename__ = "friends"

    id = Column(Integer, primary_key=True, index=True)
    is_accept = Column(Boolean, default=False)
    user_id1 = Column(Integer, ForeignKey("users.id"), nullable=False)
    user_id2 = Column(Integer, ForeignKey("users.id"), nullable=False)
    ex_diary_cnt = Column(Integer, default=0)
    last_ex_date = Column(DateTime, default=datetime.now)


__all__ = ["Friend", "Base"]
