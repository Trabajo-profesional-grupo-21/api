import redis
from .config import settings

class Redis:
    client = None

redis_instance = Redis()

async def connect_to_redis():
    redis_instance.client = redis.Redis(
        host = settings.REDIS_HOST,
        port = 10756,
        password = settings.REDIS_PASSWORD
    )

    print("Connected to Redis")


async def get_redis():
    if redis_instance.client is None:
        await connect_to_redis()
    return redis_instance.client
