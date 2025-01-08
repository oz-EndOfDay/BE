from collections import UserList
from datetime import datetime, timedelta
from typing import Any

from fastapi import HTTPException
from sqlalchemy import Nullable, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from .models import User
from .schema.request import UpdateRequestBody
from .schema.response import SocialUser
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

    async def create_user_from_social(self, social_user: SocialUser) -> int:
        print("social user 생성")
        new_user = User(
            nickname=social_user.nickname,
            email=social_user.email,
            name="",
            password="",
            is_active=social_user.is_active,
            provider=social_user.provider,
        )
        self.session.add(new_user)
        await self.session.commit()
        await self.session.refresh(new_user)

        return new_user.id

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

    async def is_active_user(self, user_id: int) -> None:
        user = await self.get_user_by_id(user_id)
        if user is None:
            raise UserNotFoundException(f"User with id {user_id} not found")
        user.is_active = True
        await self.session.commit()

    # 사용자 정보 수정
    async def update_user(self, user_id: int, user_data: dict[str, Any]) -> User:
        user = await self.get_user_by_id(user_id)
        if user is None:
            raise UserNotFoundException(f"User with id {user_id} not found")

        # 사용자 정보 업데이트
        user.name = user_data.get("name", user.name)
        user.nickname = user_data.get("nickname", user.nickname)
        user.img_url = user_data.get("img_url", user.img_url)
        user.introduce = user_data.get("introduce", user.introduce)
        user.is_active = user_data.get("is_active", user.is_active)

        # 수정 날짜 업데이트
        user.modified_at = datetime.now().replace(tzinfo=None)

        # 비밀번호 처리
        if "password" in user_data and user_data["password"]:
            hashed = hash_password(user_data["password"])
            user.password = hashed  # 비밀번호 업데이트

        # 변경 사항 커밋
        await self.session.commit()

        return user

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

    # 메일이나 닉네임으로 유저 검색
    async def search_user(self, word: str) -> list[User]:
        query = (
            select(User)
            .where(User.is_active.is_(True))
            .filter(or_(User.nickname.ilike(word), User.email.ilike(word)))
        )

        result = await self.session.execute(query)
        return list(result.scalars().all())
