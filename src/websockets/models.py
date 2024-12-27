from sqlalchemy import Column, DateTime, ForeignKey, Integer, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()  # Base는 declarative_base()로 생성된 객체입니다.


# mypy에서 이를 클래스 타입으로 인식하게 하기 위해 선언적인 메타클래스인 DeclarativeMeta를 사용
class Websockets(Base):

    __tablename__ = "websockets"

    message_id = Column(Integer, primary_key=True)
    message = Column(Text)
    created_at = Column(DateTime, default=func.now())  # 기본값으로 현재 시간 설정
    friend_id = Column(Integer, ForeignKey("friends.friend_id"))  # 예시로 외래 키 관계 설정
    user_id = Column(Integer, ForeignKey("users.user_id"))  # 예시로 외래 키 관계 설정
