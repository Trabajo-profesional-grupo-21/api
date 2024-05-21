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

    # def get_all_users(db: Session, skip: int = 0, limit: int = 100, sortBy: str = None, sortDirection: str = None):
    #     users = crud.user.get_all(db, skip, limit, sortBy, sortDirection)
    #     return users

    # def get_user(db: Session, wallet_id: str):
    #     user = crud.user.get(db, wallet_id)
    #     if not user:
    #         raise UserNotFound()
    #     return user

    # def update_user(db: Session, wallet_id: str, user_data: UserBase):
    #     current_user = crud.user.get(db, wallet_id)
    #     if not current_user:
    #         raise UserNotFound(message="Cannot update nonexistent user")
 
    #     user = crud.user.update(db, current_user, user_data)
    #     return user


    # def delete_user(db: Session, wallet_id: str):
    #     current_user = crud.user.get(db, wallet_id)
    #     if not current_user:
    #         raise UserNotFound(message="Cannot remove nonexistent user")
 
    #     return crud.user.remove(db, wallet_id)