"""Methods for brokering messages using RabbitMQ"""
import pika


def broadcast(host, body, exchange, credentials=None):
    """Sends a message to the host to go to
    be added to the exchange 'exchange'. Taken from
    https://www.rabbitmq.com/tutorials/tutorial-three-python.html"""

    if not credentials:
        credentials = pika.PlainCredentials('guest', 'guest')

    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host=host,
            credentials=credentials
        )
    )
    channel = connection.channel()

    channel.exchange_declare(
        exchange=exchange,
        exchange_type='fanout')

    channel.basic_publish(
        exchange=exchange,
        routing_key='',
        body=body
    )
    connection.close()


def receive(host, exchange, callback, credentials=None):
    """Waits for messages from the exchange on host
    and runs callback based on the output"""

    if not credentials:
        credentials = pika.PlainCredentials('guest', 'guest')

    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host=host,
            credentials=credentials
        )
    )
    channel = connection.channel()

    channel.exchange_declare(
        exchange=exchange,
        exchange_type='fanout'
    )

    result = channel.queue_declare(exclusive=True)
    queue_name = result.method.queue

    channel.queue_bind(
        exchange=exchange,
        queue=queue_name
    )

    channel.basic_consume(
        callback,
        queue=queue_name,
        no_ack=True
    )

    channel.start_consuming()
