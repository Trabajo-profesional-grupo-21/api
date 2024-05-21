from motor.motor_asyncio import AsyncIOMotorDatabase
from ..schemas.user import UserBase
from ..exceptions.commons import DbError


async def create(db: AsyncIOMotorDatabase, user_data: UserBase) -> UserBase:
    try:
        await db["users"].insert_one(user_data.dict())
        return user_data
    except Exception as e:
        print(e)
        raise DbError(message=e)


async def find(db: AsyncIOMotorDatabase, email: str) -> UserBase:
    try:
        result = await db["users"].find_one({"email": email})
        return result
    except Exception as e:
        raise DbError(message=e)