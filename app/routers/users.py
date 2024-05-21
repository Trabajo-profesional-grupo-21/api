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

# @router.get("/", response_model=List[UserInDBBase])
# async def find_all_users(
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_admin),
#     pagination: dict = Depends(pagination_params),
#     sorting: dict = Depends(sorting_params)
# ):
#     """
#     Find all users.
#     """
#     return UserService.get_all_users(db, pagination["skip"], pagination["limit"], sorting["sortBy"], sorting["sortDirection"])


# @router.get("/me", response_model=UserInDBBase)
# async def find_me(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> Any:
#     """
#     Get current user.
#     """
#     return current_user


# @router.get("/{wallet_id}", response_model=UserInDBBase)
# async def find_user(wallet_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user_or_admin)) -> Any:
#     """
#     Get a specific user by wallet_id.
#     """
#     return UserService.get_user(db, wallet_id)


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=UserBase)
async def create_user(user_data: UserBase, db: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Creates a new user.
    """
    return await UserService.create_user(db, user_data)


# @router.put("/{wallet_id}", status_code=status.HTTP_200_OK, response_model=UserInDBBase)
# async def update_user(user_data: UserBase, wallet_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user_or_admin)):
#     """
#     Updates user.
#     """
#     return UserService.update_user(db, wallet_id, user_data)


# @router.delete("/{wallet_id}" , status_code=status.HTTP_204_NO_CONTENT)
# async def delete_user(wallet_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user_or_admin)):
#     """
#     Deletes a user.
#     """
#     UserService.delete_user(db, wallet_id)
#     return None