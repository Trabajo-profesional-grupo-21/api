from motor.motor_asyncio import AsyncIOMotorDatabase
from ..exceptions.commons import DbError


async def create(db: AsyncIOMotorDatabase, user_id: str, file_name: str, thumbnail: str, extra_data = {}, type: str = 'video'):
    try:

        data = {
            "user_id": user_id,
            "type": type,
            "file_name": file_name,
            "thumbnail": thumbnail,
            "extra_data": extra_data,
            "stimulus": None,
            "stimulus_thumbnail": None,
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


async def find_all_data(db: AsyncIOMotorDatabase, user_id: str, file_type: str):
    try:
        cursor = db["data"].find({"user_id": user_id, "type": file_type})
        result = await cursor.to_list(None)
        return result
    except Exception as e:
        raise DbError(message=e)
    
async def delete(db: AsyncIOMotorDatabase, user_id: str, file_name: str):
    try:
        result = await db["data"].find_one_and_delete({"user_id": user_id, "file_name": file_name})
        return result
    except Exception as e:
        raise DbError(message=e)

async def assign_stimulus(db: AsyncIOMotorDatabase, user_id: str, file_name: str, stimulus_name: str, stimulus_thumbnail: str):
    try:

        data = db["data"].find_one_and_update({"user_id": user_id, "file_name": file_name}, 
                                                    {"$set": {"stimulus": stimulus_name, "stimulus_thumbnail": stimulus_thumbnail}}, return_document=True)
        if data is None:
            raise Exception("File Not Found")

        return data
    except Exception as e:
         raise Exception(f"Database Error [{e}]")