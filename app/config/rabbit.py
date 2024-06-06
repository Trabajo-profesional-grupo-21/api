from common.async_connection import AsyncConnection
import os

class Rabbit:
    connection = None
    output_queue = None

rabbit = Rabbit()

async def connect_to_rabbit():
    remote_rabbit = os.getenv('REMOTE_RABBIT', False)
    if remote_rabbit:
        connection = AsyncConnection(host=os.getenv('RABBIT_HOST'), 
                                port=os.getenv('RABBIT_PORT'),
                                virtual_host=os.getenv('RABBIT_VHOST'), 
                                user=os.getenv('RABBIT_USER'), 
                                password=os.getenv('RABBIT_PASSWORD'))
    else:
        connection = AsyncConnection()

    await connection.connect()
    rabbit.output_queue = await connection.Publisher("frames", "fanout")
    print(f"Connection: {rabbit.output_queue}")

    print("Connected to RabbitMQ")

async def get_rabbit():
    if rabbit.output_queue is None:
        await connect_to_rabbit()
    return rabbit.output_queue