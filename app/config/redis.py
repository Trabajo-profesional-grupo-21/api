import redis
from .config import settings

class Redis:
    client = None

redis_instance = Redis()

async def connect_to_redis():
    try:
        redis_instance.client = redis.Redis(
            host = settings.REDIS_HOST,
            port = settings.REDIS_PORT,
            password = settings.REDIS_PASSWORD
        )
        print("Connected to Redis")

    except Exception as e:
        print(f"Redis connection failed: {e}")


async def get_redis():
    if redis_instance.client is None:
        await connect_to_redis()
    return redis_instance.client
