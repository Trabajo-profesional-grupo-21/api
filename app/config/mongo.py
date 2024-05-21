# db.py
import motor.motor_asyncio
from .config import settings

class MongoDB:
    client: motor.motor_asyncio.AsyncIOMotorClient = None
    db = None

mongodb = MongoDB()

async def connect_to_mongo():
    mongodb.client = motor.motor_asyncio.AsyncIOMotorClient(settings.MONGODB_URL)
    mongodb.db = mongodb.client[settings.MONGODB_DB_NAME]
    print("Connected to MongoDB")

async def close_mongo_connection():
    mongodb.client.close()
    print("Closed MongoDB connection")

async def get_db():
    if mongodb.db is None:
        await connect_to_mongo()
    return mongodb.db
