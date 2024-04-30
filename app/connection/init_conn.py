from common.connection import Connection
import os
from dotenv import load_dotenv
import aiormq

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
    connection = Connection(host='moose.rmq.cloudamqp.com', port=5672,
                             virtual_host="zacfsxvy", user="zacfsxvy", password="zfCu8hS9snVGmySGhtvIVeMi6uvYssih")
    # connection = Connection(host="rabbitmq-0.rabbitmq.default.svc.cluster.local", port=5672)
    output_queue = connection.Publisher("frames", "fanout")
    input_queue = connection.Consumer(queue_name="ordered_batches")

    return connection, output_queue, input_queue