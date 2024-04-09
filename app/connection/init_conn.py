from .Connection import Connection

def init_conn():
    connection = Connection()
    output_queue = connection.Publisher("frames", "fanout")
    input_queue = connection.Consumer(queue_name="ordered_batches")

    return connection, output_queue, input_queue