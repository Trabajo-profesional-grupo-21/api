from jose import jwt
from passlib.context import CryptContext
from ..crud import user_crud
from typing import Union, Any
from datetime import datetime, timedelta
from ..config.config import settings
from ..schemas.user import UserBase
from motor.motor_asyncio import AsyncIOMotorDatabase

password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    def get_hash(password: str) -> str:
        return password_context.hash(password)

    def verify_password(password: str, hashed_password: str) -> bool:
        return password_context.verify(password, hashed_password)

    def create_access_token(subject: Union[str, Any]) -> str:
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        expire = datetime.utcnow() + access_token_expires

        to_encode = {"exp": expire, "sub": str(subject)}
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        return encoded_jwt

    async def authenticate_user(db: AsyncIOMotorDatabase, email: str, password: str) -> UserBase:
        user = await user_crud.find(db, email)
        # print(user)
        if not user:
            return False
        if not password_context.verify(password, user["password"]):
            return False
        return user
        