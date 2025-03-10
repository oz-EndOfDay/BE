from datetime import datetime
from typing import Any, Optional

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship

from src.config.database.orm import Base
from src.ex_diary.models import ExDiary


class Friend(Base):
    __tablename__ = "friends"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True)
    user_id1 = Column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=False
    )
    user_id2 = Column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=False
    )

    is_accept = Column(Boolean, default=False)
    ex_diary_cnt = Column(Integer, default=0)
    last_ex_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.now)

    # 관계 설정
    user1 = relationship("User", foreign_keys=[user_id1])  # type: ignore
    user2 = relationship("User", foreign_keys=[user_id2])  # type: ignore
    ex_diaries = relationship("ExDiary", back_populates="friend", cascade="all, delete-orphan")  # type: ignore

    @hybrid_property
    def user1_nickname(self) -> Optional[str]:
        if self.user_id1:
            return self.user1.nickname  # type: ignore
        return None

    @hybrid_property
    def user2_nickname(self) -> Optional[str]:
        if self.user_id2:
            return self.user2.nickname  # type: ignore
        return None


__all__ = ["Friend", "Base"]
