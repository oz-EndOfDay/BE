from datetime import datetime, timedelta, timezone
from typing import Dict, Optional, Union
from urllib.parse import urlparse

import boto3
import httpx
import jwt
from botocore.exceptions import ClientError
from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Request,
    Response,
    UploadFile,
    status,
)
from fastapi.security import HTTPAuthorizationCredentials
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import RedirectResponse

from blacklist import blacklist_token
from src.config import Settings
from src.config.database.connection import get_async_session
from src.user.models import User
from src.user.repository import UserNotFoundException, UserRepository
from src.user.schema.request import CreateRequestBody, LoginRequest, UserEmailRequest
from src.user.schema.response import (
    BasicResponse,
    JWTResponse,
    KakaoCallbackResponse,
    SocialUser,
    UserInfo,
    UserMeDetailResponse,
    UserMeResponse,
    UserSearchResponse,
)
from src.user.service.authentication import (
    ALGORITHM,
    authenticate,
    create_verification_token,
    decode_access_token,
    encode_access_token,
    encode_refresh_token,
    hash_password,
    verify_password,
)
from src.user.service.smtp import send_email

settings = Settings()

router = APIRouter(prefix="/users", tags=["User"])


# 유저 생성 (회원가입)
@router.post(
    "", summary="회원 가입(유저생성)", response_model=UserMeResponse, status_code=201
)
async def create_user(
    request: Request,
    user_data: CreateRequestBody,
    session: AsyncSession = Depends(get_async_session),
) -> UserMeResponse:
    user_repo = UserRepository(session)  # UserRepository 인스턴스 생성

    new_user = User(
        name=user_data.name,
        nickname=user_data.nickname,
        email=user_data.email,
        password=hash_password(user_data.password),  # 비밀번호 해싱 처리
        is_active=False,
        provider="",
    )

    created_user = await user_repo.create_user(new_user)  # 올바른 메서드 호출
    # 인증 토큰 생성
    token = create_verification_token(user_data.email)
    # 인증 링크 생성
    verification_link = f"{request.base_url}users/email_verify/{token}"

    await send_email(
        to=user_data.email,
        subject="Email Verification",
        body=f"Please verify your email by clicking the following link: {verification_link}",
    )

    return UserMeResponse(
        id=created_user.id,
        name=created_user.name,
        nickname=created_user.nickname,
    )


@router.get(
    "",
    summary="로그인한 유저 상세 정보 가져오기",
    response_model=UserMeDetailResponse,
    status_code=200,
)
async def get_users(
    user_id: int = Depends(authenticate),  # 인증된 사용자 ID
    session: AsyncSession = Depends(get_async_session),
) -> UserMeDetailResponse:
    user_repo = UserRepository(session)

    user = await user_repo.get_user_by_id(user_id)

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    return UserMeDetailResponse(
        id=user.id,
        name=user.name,
        nickname=user.nickname,
        email=user.email,
        introduce=user.introduce,
        img_url=user.img_url,
        created_at=user.created_at,
    )


# 패스워드 분실
@router.post(
    "/forgot_password",
    summary="패스워드 분실 시 임시 비밀번호 발급",
    response_model=BasicResponse,
)
async def forgot_password(
    email: str, session: AsyncSession = Depends(get_async_session)
) -> BasicResponse:

    user_repo = UserRepository(session)
    temp_password = await user_repo.forgot_password(email)

    await send_email(
        to=email,
        subject="Forgot Password",
        body=f"Your temporary password is {temp_password}. Please change your password after logging in with your temporary password.",
    )

    return BasicResponse(
        message="Your temporary password has been changed successfully.",
        status="success",
    )


# 회원가입 이메일 인증
@router.get("/email_verify/{token}", summary="올바른(실제 사용중) 이메일 검증")
async def verify_email(
    token: str, session: AsyncSession = Depends(get_async_session)
) -> Dict[str, str]:

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("email")

        if email is None:
            raise HTTPException(status_code=400, detail="Invalid token")

        user_repo = UserRepository(session)
        user = await user_repo.get_user_by_email(email)  # 이메일로 사용자 조회

        if user is None:
            raise HTTPException(status_code=404, detail="Email not found")

        if not user.id is None:
            await user_repo.is_active_user(user.id)

        return {"message": "Email verified successfully!"}

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=400, detail="Token has expired")

    except jwt.PyJWTError:
        raise HTTPException(status_code=400, detail="Invalid token")


# 로그인 엔드포인트 구현 (비동기)
@router.post(
    "/login",
    summary="로그인",
    response_model=JWTResponse,
    status_code=status.HTTP_200_OK,
)
async def login_handler(
    login_data: LoginRequest,
    response: Response,
    session: AsyncSession = Depends(get_async_session),
) -> JWTResponse:
    user_repo = UserRepository(session)
    user = await user_repo.get_user_by_email(login_data.email)

    if user is not None and user.id is not None:
        if user.is_active:
            if verify_password(
                plain_password=login_data.password, hashed_password=user.password
            ):
                refresh_token = encode_refresh_token(user.id)
                access_token = encode_access_token(user_id=user.id)

                response.set_cookie(
                    key="access_token",
                    value=access_token,
                    httponly=True,
                    secure=True,  # HTTPS 사용하므로 True 유지
                    samesite="none",  # 크로스 도메인이므로 none으로 설정
                    path="/",
                    max_age=3600,  # 1시간
                    expires=datetime.now(timezone.utc)
                    + timedelta(hours=1),  # expires 추가
                    # domain="api.endofday.store",
                )

                response.set_cookie(
                    key="refresh_token",
                    value=refresh_token,
                    httponly=True,
                    secure=True,
                    samesite="none",
                    path="/",
                    max_age=30 * 24 * 3600,  # 30일
                    expires=datetime.now(timezone.utc)
                    + timedelta(days=30),  # expires 추가
                    # domain="api.endofday.store",
                )

                return JWTResponse(
                    access_token=access_token,
                    refresh_token=refresh_token,
                )

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect password",
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 인증을 받지 않았거나 회원 탈퇴된 계정입니다.",
        )

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="User not found",
    )


# 로그아웃 엔드포인트
@router.post(
    "/logout",
    summary="로그아웃",
    status_code=status.HTTP_200_OK,
    response_model=BasicResponse,
)
async def logout_handler(request: Request, response: Response) -> BasicResponse:
    try:
        access_token = request.cookies.get("access_token")
        refresh_token = request.cookies.get("refresh_token")
        if access_token is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="No token provided"
            )
        # JWT 토큰 디코딩
        payload = decode_access_token(access_token)
        user_id = payload.get("user_id")

        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
            )

        # 토큰을 블랙리스트에 추가
        if access_token:
            await blacklist_token(access_token)
        if refresh_token:
            await blacklist_token(refresh_token)
        # 클라이언트의 쿠키 삭제
        response.delete_cookie(key="access_token")
        response.delete_cookie(key="refresh_token")
        return BasicResponse(message="로그아웃 되었습니다.", status="success")

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )


@router.get(
    "/kakao/login",
    status_code=status.HTTP_200_OK,
)
def kakao_social_login_handler() -> Response:
    return RedirectResponse(
        "https://kauth.kakao.com/oauth/authorize"
        f"?client_id={settings.KAKAO_CLIENT_ID}"
        f"&redirect_uri={settings.KAKAO_REDIRECT_URI}"
        f"&response_type=code",
    )


@router.get("/kakao/callback", response_model=KakaoCallbackResponse)
async def callback(
    code: str,
    session: AsyncSession = Depends(get_async_session),
) -> dict[str, str | UserInfo]:
    token_url = "https://kauth.kakao.com/oauth/token"
    async with httpx.AsyncClient() as client:
        response = await client.post(
            token_url,
            data={
                "grant_type": "authorization_code",
                "client_id": settings.KAKAO_CLIENT_ID,
                "redirect_uri": settings.KAKAO_REDIRECT_URI,
                "client_secret": settings.KAKAO_CLIENT_SECRET,
                "code": code,
            },
        )

    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code, detail="Failed to get access token"
        )

    token_data = response.json()
    access_token = token_data.get("access_token")

    # 사용자 정보 요청
    user_info_url = "https://kapi.kakao.com/v2/user/me"
    async with httpx.AsyncClient() as client:
        user_info_response = await client.get(
            user_info_url, headers={"Authorization": f"Bearer {access_token}"}
        )

    if user_info_response.status_code != 200:
        raise HTTPException(
            status_code=user_info_response.status_code, detail="Failed to get user info"
        )

    user_info = user_info_response.json()
    user_email = user_info.get("kakao_account", {}).get("email")

    if not user_email:
        raise HTTPException(status_code=400, detail="Email not provided by Kakao")

    user_repo = UserRepository(session)
    existing_user = await user_repo.get_user_by_email(user_email)

    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = SocialUser(
        email=user_email,
        nickname=f'kakao_{user_info.get("id")}',
        provider="kakao",
        is_active=True,
    )
    user_id = await user_repo.create_user_from_social(new_user)

    user_data = UserInfo(
        id=user_info.get("id"),
        nickname=f"kakao_{user_info.get('id')}",
        email=user_info.get("kakao_account", {}).get("email"),
        connected_at=user_info.get("connected_at"),
    )

    access_token = encode_access_token(user_id=user_id)
    refresh_token = encode_refresh_token(user_id=user_id)

    return {
        "user_info": user_data,
        "access_token": access_token,
        "refresh_token": refresh_token,
    }


# 사용자 정보 수정
@router.put(
    path="",
    summary="회원 정보 수정",
    status_code=status.HTTP_200_OK,
    response_model=UserMeResponse,
)
async def update_user(
    user_id: int = Depends(authenticate),  # 인증된 사용자 ID
    name: str = Form(...),
    nickname: str = Form(...),
    password: str = Form(...),
    introduce: str = Form(...),
    image: Union[UploadFile, str] = File(default=None),
    session: AsyncSession = Depends(get_async_session),
) -> UserMeResponse | dict[str, str]:
    user_repo = UserRepository(session)  # UserRepository 인스턴스 생성

    user = await user_repo.get_user_by_id(user_id)
    s3_client = boto3.client(
        "s3",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_REGION,
    )
    img_url: Optional[str] = None
    # 이미지 업로드 처리
    if image and image.filename:  # type: ignore
        # 유저의 이전 프로필 사진이 s3에 있다면 삭제
        if user and user.img_url:
            parsed_url = urlparse(user.img_url)
            s3_key = parsed_url.path.lstrip("/")
            try:
                # S3에서 객체 삭제
                s3_client.delete_object(Bucket=settings.S3_BUCKET_NAME, Key=s3_key)
                print("Previous image deleted successfully.")
            except s3_client.exceptions.NoSuchKey:
                print("Previous image not found.")

        try:
            # 파일 포인터 초기화
            image.file.seek(0)  # type: ignore

            # 고유한 파일명 생성
            image_filename = (
                f"profile_{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            )

            # S3에 업로드
            s3_key = f"profiles/{image_filename}"
            s3_client.upload_fileobj(
                image.file,  # type: ignore
                settings.S3_BUCKET_NAME,
                s3_key,
                ExtraArgs={"ContentType": image.content_type},  # type: ignore
            )

            # 공개 URL 생성
            img_url = f"https://{settings.S3_BUCKET_NAME}.s3.{settings.AWS_REGION}.amazonaws.com/{s3_key}"

        except ClientError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"S3 업로드 오류: {str(e)}",
            )

    # 사용자 데이터 업데이트 (img_url 포함)
    user_data_dict = {
        "name": name,
        "nickname": nickname,
        "password": password,
        "introduce": introduce,
        "img_url": img_url,  # S3에서 받은 URL 또는 None
    }

    try:
        updated_user = await user_repo.update_user(user_id, user_data_dict)

    except UserNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    return UserMeResponse(
        id=updated_user.id,
        name=updated_user.name,
        nickname=updated_user.nickname,
    )


# soft delete 방식으로 삭제 일자를 db에 입력 후 7일 지난 데이터는 안보이도록 함.
@router.delete(
    path="/delete",
    summary="회원 탈퇴(Soft Delete)",
    status_code=status.HTTP_200_OK,
    response_model=None,
)
async def delete_user(
    user_id: int = Depends(authenticate),
    session: AsyncSession = Depends(get_async_session),
) -> dict[str, str]:
    user_repo = UserRepository(session)
    try:
        await user_repo.soft_delete_user(user_id)
    except UserNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    return {
        "message": "회원탈퇴가 처리되었습니다. 데이터는 7일간 보관됩니다.",
        "status": "success",
    }


@router.post(
    path="/recovery",
    summary="계정 복구 가능 여부",
    status_code=status.HTTP_200_OK,
    response_model=BasicResponse,
)
async def recovery_possible(
    request: Request,
    user_email: UserEmailRequest,
    session: AsyncSession = Depends(get_async_session),
) -> BasicResponse:
    user_repo = UserRepository(session)
    user = await user_repo.get_user_by_email(user_email.email)

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    if user.email is None:
        raise HTTPException(status_code=404, detail="User email is not available")
    if user.is_active:
        raise HTTPException(status_code=403, detail="Account is active")
    if user.deleted_at and user.deleted_at < datetime.now() - timedelta(days=7):
        raise HTTPException(status_code=403, detail="Deleted after 7 days")

    token = create_verification_token(user.email)
    # 인증 링크 생성
    recovery_link = f"{request.base_url}users/recovery/{token}"

    await send_email(
        to=user.email,
        subject="Recovery Account",
        body=f"Please recovery your account by clicking the following link:{recovery_link}",
    )
    return BasicResponse(
        message="입력한 이메일로 계정 복구 메일을 전송하였습니다.", status="success"
    )


@router.get(
    path="/recovery/{token}",
    summary="계정 복구",
    status_code=status.HTTP_200_OK,
    response_model=BasicResponse,
)
async def recovery_account(
    token: str,
    session: AsyncSession = Depends(get_async_session),
) -> BasicResponse:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("email")

        if email is None:
            raise HTTPException(status_code=400, detail="Invalid token")

        user_repo = UserRepository(session)
        user = await user_repo.get_user_by_email(email)

        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        await user_repo.recovery_account(email)  # 이메일로 사용자 조회

        return BasicResponse(message="계정이 복구되었습니다.", status="success")

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=400, detail="Token has expired")

    except jwt.PyJWTError:
        raise HTTPException(status_code=400, detail="Invalid token")


@router.post(
    "/search", summary="닉네임이나 이메일로 유저 검색", status_code=status.HTTP_200_OK
)
async def search_users(
    word: str = Form(...), session: AsyncSession = Depends(get_async_session)
) -> list[UserSearchResponse]:
    user_repo = UserRepository(session)

    try:
        users = await user_repo.search_user(word)
        return [
            UserSearchResponse(id=user.id, nickname=user.nickname, email=user.email)
            for user in users
        ]
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# @router.post("/refresh-token", summary="리프레쉬토큰으로 액세스토큰 재발급")
# async def refresh_access_token_endpoint(
#     refresh_token: HTTPAuthorizationCredentials,
# ) -> dict[str, str]:
#     is_expired = is_refresh_token_expired(refresh_token=refresh_token.credentials)
#     if is_expired:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="리프레쉬 토큰이 만료되었습니다.",
#         )
#     new_access_token = refresh_access_token(refresh_token.credentials)
#     return {"access_token": new_access_token}
