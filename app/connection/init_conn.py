from common.connection import Connection
import aiormq
import os
from dotenv import load_dotenv

load_dotenv()

async def init_async_conn():
    connection = await aiormq.connect("amqp://guest:guest@rabbitmq:5672")
    channel = await connection.channel()

    await channel.exchange_declare(
        "frames",
        exchange_type="fanout"
    )

    return channel


def init_conn():
    remote_rabbit = os.getenv('REMOTE_RABBIT', False)
    if remote_rabbit:
        connection = Connection(host=os.getenv('RABBIT_HOST'), 
                                port=os.getenv('RABBIT_PORT'),
                                virtual_host=os.getenv('RABBIT_VHOST'), 
                                user=os.getenv('RABBIT_USER'), 
                                password=os.getenv('RABBIT_PASSWORD'))
    else:
        # connection = Connection(host="rabbitmq-0.rabbitmq.default.svc.cluster.local", port=5672)
        connection = Connection(host="rabbitmq", port=5672)

    output_queue = connection.Publisher("frames", "fanout")
    input_queue = connection.Consumer(queue_name="ordered_batches")

    return connection, output_queue, input_queue