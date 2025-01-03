import re
from datetime import datetime
from typing import Optional, Type, TypeVar

from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from config.database.orm import Base
from user.service.authentication import hash_password

T = TypeVar("T", bound="User")  # Generic type variable for the class method


class User(Base):
    __tablename__ = "users"
    __table_args__ = {"extend_existing": True}

    # id = Column(Integer, primary_key=True, index=True)
    # name = Column(String, nullable=False)
    # nickname = Column(String, unique=True, index=True, nullable=False)
    # email = Column(String, unique=True, index=True, nullable=False)
    # introduce = Column(String)
    # password = Column(String, nullable=False)
    # img_url = Column(String)
    # created_at = Column(DateTime, default=datetime.now)
    # modified_at = Column(
    #     DateTime(timezone=True), default=datetime.now, onupdate=datetime.now
    # )
    # deleted_at = Column(DateTime)
    # is_active = Column(Boolean, default=False)
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[Optional[str]] = mapped_column(nullable=True)
    nickname: Mapped[Optional[str]] = mapped_column(nullable=True)
    email: Mapped[str]
    password: Mapped[str]
    img_url: Mapped[Optional[str]] = mapped_column(nullable=True)
    introduce: Mapped[Optional[str]] = mapped_column(nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime]
    modified_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    @staticmethod
    def _is_bcrypt_pattern(password: str) -> bool:
        bcrypt_pattern = r"^\$2[aby]\$\d{2}\$[./A-Za-z0-9]{53}$"
        return re.match(bcrypt_pattern, password) is not None

    @classmethod
    def create(cls: Type[T], name: str, nickname: str, email: str, password: str) -> T:
        if cls._is_bcrypt_pattern(password):
            raise ValueError("Password must be plain text")

        hashed_password = hash_password(password)
        print("회원가입시 생성된 비밀번호:" + hashed_password)
        return cls(name=name, nickname=nickname, email=email, password=hashed_password)


__all__ = ["User", "Base"]
