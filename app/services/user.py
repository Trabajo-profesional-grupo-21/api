from typing import Any, List
from ..crud import user_crud
from motor.motor_asyncio import AsyncIOMotorDatabase
from ..schemas.user import UserBase
from .auth import AuthService
from ..exceptions.user_exceptions import UserAlreadyExists, UserNotFound

class UserService:

    async def create_user(db: AsyncIOMotorDatabase, user_data:  UserBase):
        user = await user_crud.find(db, email=user_data.email)

        if user:
            raise UserAlreadyExists()

        user_data.password = AuthService.get_hash(user_data.password)
        user = await user_crud.create(db, user_data)

        return user