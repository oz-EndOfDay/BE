import re
from datetime import datetime
from typing import Type, TypeVar

from sqlalchemy import Column, DateTime, Integer, String

from src.config.database.orm import Base
from src.user.service.authentication import hash_password

T = TypeVar("T", bound="User")  # Generic type variable for the class method


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

    @staticmethod
    def _is_bcrypt_pattern(password: str) -> bool:
        bcrypt_pattern = r"^\$2[aby]\$\d{2}\$[./A-Za-z0-9]{53}$"
        return re.match(bcrypt_pattern, password) is not None

    @classmethod
    def create(cls: Type[T], name: str, nickname: str, email: str, password: str) -> T:
        if cls._is_bcrypt_pattern(password):
            raise ValueError("Password must be plain text")

        hashed_password = hash_password(password)
        return cls(name=name, nickname=nickname, email=email, password=hashed_password)


__all__ = ["User", "Base"]
