from motor.motor_asyncio import AsyncIOMotorDatabase
from ..exceptions.commons import DbError


""""""

async def create(db: AsyncIOMotorDatabase, email: str, video_name: str):
    try:
        
        result = await db["videos"].find_one({"user_id": email})
        new_element = {
            "name": video_name,
            "data": {},
        }

        if result is not None:
            data = await db["videos"].find_one_and_update({"user_id": email}, {"$push": {"videos": new_element}}, return_document=True)
        else:
            data = {
                "user_id": email,
                "videos": [new_element]
            }
            await db["videos"].insert_one(data)
        return data
    except Exception as e:
        raise DbError(message=e)


async def find(db: AsyncIOMotorDatabase, email: str, video_name: str):
    try:
        result = await db["videos"].find_one({"user_id": email})

        if result is None:
            return None

        for video in result["videos"]:
            if video["name"] == video_name:
                return video

        return None
    except Exception as e:
        raise DbError(message=e)