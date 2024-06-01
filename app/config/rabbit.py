import aiormq

class Rabbit:
    connection = None
    channel = None

rabbit = Rabbit()

async def connect_to_rabbit():
    rabbit.connection = await aiormq.connect("amqp://guest:guest@rabbitmq:5672")
    rabbit.channel = await rabbit.connection.channel()

    await rabbit.channel.exchange_declare(
        "frames",
        exchange_type="fanout"
    )

    print("Connected to RabbitMQ")
    # return rabbit.connection


async def get_rabbit():
    if rabbit.channel is None:
        await connect_to_rabbit()
    return rabbit.channel