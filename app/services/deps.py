from ..config.mongo import get_db
from motor.motor_asyncio import AsyncIOMotorDatabase
from fastapi import Query, Depends
from typing import Optional, Annotated


from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from pydantic import ValidationError
from ..config.config import settings
from ..schemas.token import TokenPayload
from ..crud import user_crud

from ..exceptions.user_exceptions import UserNotFound
from ..exceptions.auth_exceptions import InvalidCredentials, NotEnoughPrivileges
from ..exceptions.commons import InvalidParameter


oauth2 = OAuth2PasswordBearer(
    tokenUrl="/login"
)

async def get_current_user(db: AsyncIOMotorDatabase = Depends(get_db), token: str = Depends(oauth2)):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        token_data = TokenPayload(**payload)
    except (jwt.JWTError, ValidationError):
        raise InvalidCredentials(message="Invalid access token")

    user = await user_crud.find(db, token_data.sub)
    if not user:
        raise UserNotFound()
    return user

# # def get_current_user_or_admin(wallet_id: str, current_user: User = Depends(get_current_user)):
# #     if crud.user.is_admin(current_user) or current_user.wallet_id == wallet_id:
# #         return current_user
# #     else:
# #         raise NotEnoughPrivileges()

# # def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
# #     if not crud.user.is_admin(current_user):
# #         raise NotEnoughPrivileges()
# #     return current_user