from fastapi import APIRouter, Depends, status
from typing import Any
from fastapi.security import OAuth2PasswordRequestForm
from ..config.mongo import get_db
from ..schemas.token import Token
from ..services.auth import AuthService
from ..exceptions.auth_exceptions import InvalidCredentials
from motor.motor_asyncio import AsyncIOMotorDatabase
from ..schemas.user import UserBase

router = APIRouter(
    tags=["Auth"]
)

@router.post("/login", response_model=Token, status_code=status.HTTP_200_OK)
async def login_access_token(db: AsyncIOMotorDatabase = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()) -> Any:
    """
    OAuth2 compatible token login, get an access token
    """
    user = await AuthService.authenticate_user(db, email=form_data.username, password=form_data.password)
    if not user:
        raise InvalidCredentials()

    access_token = AuthService.create_access_token(user["email"])

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }