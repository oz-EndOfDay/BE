from datetime import datetime, timedelta

from fastapi import HTTPException
from sqlalchemy import Nullable
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from .models import User
from .schema.request import UpdateRequestBody
from .service.authentication import generate_password, hash_password


class UserNotFoundException(Exception):
    pass


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    # 회원 가입 유저 생성
    async def create_user(self, user: User) -> User:
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)  # 새로 생성된 객체를 갱신
        return user

    # 아이디로 사용자 조회
    async def get_user_by_id(self, user_id: int) -> User | None:
        stmt = select(User).where(User.id == user_id)
        result = await self.session.execute(stmt)
        user = result.scalar_one_or_none()

        return user

    # 이메일로 사용자 조회
    async def get_user_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email)
        result = await self.session.execute(stmt)
        user = result.scalar_one_or_none()

        return user

    # 사용자 정보 수정
    async def update_user(self, user_id: int, user_data: UpdateRequestBody) -> User:
        user = await self.get_user_by_id(user_id)
        if user is None:
            raise UserNotFoundException(f"User with id {user_id} not found")

        # 사용자 정보 업데이트
        user.name = user_data.name if user_data.name else user.name
        user.nickname = user_data.nickname if user_data.nickname else user.nickname
        user.img_url = user_data.img_url if user_data.img_url else user.img_url
        user.introduce = user_data.introduce if user_data.introduce else user.introduce
        user.is_active = user_data.is_active if user_data.is_active else user.is_active
        user.modified_at = datetime.now().replace(tzinfo=None)
        if user_data.password:
            hashed = hash_password(user_data.password)
            user_data.password = hashed
        else:
            user.password = user.password
        print(user.password)

        update_data = user_data.dict(exclude_unset=True)
        for key, value in update_data.items():
            if value is not None:  # None이 아닌 값만 업데이트
                setattr(user, key, value)

        await self.session.commit()
        return user
        #

    # 회원 탈퇴 소프트 딜리트
    async def soft_delete_user(self, user_id: int) -> None:
        user = await self.get_user_by_id(user_id)
        if user is None:
            raise UserNotFoundException(f"User with id {user_id} not found")

        user.deleted_at = datetime.now()  # Soft delete 처리
        user.is_active = False
        await self.session.commit()

    # 비밀번호 분실
    async def forgot_password(self, user_email: str) -> str:
        user = await self.get_user_by_email(user_email)
        if user is None:
            raise UserNotFoundException(f"User with email {user_email} not found")
        temp_password = generate_password()
        user.password = hash_password(temp_password)
        await self.session.commit()
        return temp_password

    # 계정 복구
    async def recovery_account(self, user_email: str) -> None:
        user = await self.get_user_by_email(user_email)
        if user is None:
            raise UserNotFoundException(f"User with email {user_email} not found")
        user.is_active = True
        user.deleted_at = None
        await self.session.commit()
