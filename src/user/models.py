from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String

from src.config.database.orm import Base


class User(Base):

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    nickname = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    introduce = Column(String)
    password = Column(String, nullable=False)
    img_url = Column(String)
    created_at = Column(DateTime, default=datetime.now)
    modified_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    deleted_at = Column(DateTime)


__all__ = ["User", "Base"]
