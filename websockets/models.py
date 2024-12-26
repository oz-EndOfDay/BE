# websockets/models.py
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    message_id = Column(Integer, primary_key=True)
    message = Column(Text)
    created_at = Column(DateTime, default=func.now())  # 기본값으로 현재 시간 설정
    friend_id = Column(Integer, ForeignKey("friends.friend_id"))  # 예시로 외래 키 관계 설정
    user_id = Column(Integer, ForeignKey("users.user_id"))  # 예시로 외래 키 관계 설정
