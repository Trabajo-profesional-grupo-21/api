import asyncio
from common.async_connection import AsyncConnection
from .config import settings

class Rabbit:
    connection = None
    output_queue = None

rabbit = Rabbit()

async def connect_to_rabbit(retries=10, delay=5):
    remote_rabbit = settings.REMOTE_RABBIT
    if remote_rabbit:
        connection = AsyncConnection(host=settings.RABBIT_HOST, 
                                port=settings.RABBIT_PORT,
                                virtual_host=settings.RABBIT_VHOST, 
                                user=settings.RABBIT_USER, 
                                password=settings.RABBIT_PASSWORD)
    else:
        connection = AsyncConnection()

    for attempt in range(retries):

        try:
            await connection.connect()
            rabbit.output_queue = await connection.Publisher("frames", "fanout")
            await rabbit.output_queue.init()

            print("Connected to RabbitMQ")
            break

        except Exception as e:
            print(f"RabbitMQ connection attempt {attempt + 1} failed: {e}")
            if attempt < retries - 1:
                await asyncio.sleep(delay)
            else:
                raise e

async def get_rabbit():
    if rabbit.output_queue is None:
        await connect_to_rabbit()
    return rabbit.output_queue