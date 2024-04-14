from common.connection import Connection

def init_conn():
    connection = Connection(host='moose.rmq.cloudamqp.com', port=5672,
                             virtual_host="zacfsxvy", user="zacfsxvy", password="zfCu8hS9snVGmySGhtvIVeMi6uvYssih")
    output_queue = connection.Publisher("frames", "fanout")
    input_queue = connection.Consumer(queue_name="ordered_batches")

    return connection, output_queue, input_queue