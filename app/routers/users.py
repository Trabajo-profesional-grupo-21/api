from fastapi import APIRouter, Depends, status
from typing import Any, List
# from ..schemas.user import UserInDBBase, UserCreate, UserBase
# from ..services.deps import get_db, pagination_params, sorting_params, get_current_admin, get_current_user, get_current_user_or_admin
from ..services.user import UserService
from ..config.mongo import get_db
from motor.motor_asyncio import AsyncIOMotorDatabase
from ..schemas.user import UserBase

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=UserBase)
async def create_user(user_data: UserBase, db: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Creates a new user.
    """
    return await UserService.create_user(db, user_data)
