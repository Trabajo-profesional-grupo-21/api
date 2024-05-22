from motor.motor_asyncio import AsyncIOMotorDatabase
from ..exceptions.commons import DbError


""""""

async def create(db: AsyncIOMotorDatabase, user_id: str, file_name: str, extra_data = {}, type: str = 'video'):
    try:

        data = {
            "user_id": user_id,
            "type": type,
            "file_name": file_name,
            "extra_data": extra_data,
            "data": {}
        }

        await db["data"].insert_one(data)
        return data
    except Exception as e:
        raise DbError(message=e)


async def find(db: AsyncIOMotorDatabase, user_id: str, file_name: str):
    try:
        result = await db["data"].find_one({"user_id": user_id, "file_name": file_name})

        return result
    except Exception as e:
        raise DbError(message=e)