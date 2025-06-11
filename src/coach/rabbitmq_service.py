import pika
import json 
from wod_service import create_wod_for_user
import random

def on_message(channel, method_frame, header_frame, body):
    data = json.loads(body)
    user_email = data.get("user_email")
    date = data.get("date")
    
    if user_email and date:
        if random.random() < 0.2:
            print("Oops something went wrong")
            channel.basic_nack(delivery_tag=method_frame.delivery_tag, requeue=True) 
            return

        create_wod_for_user(user_email, date)
        channel.basic_ack(delivery_tag=method_frame.delivery_tag)
    else:
        channel.basic_nack(delivery_tag=method_frame.delivery_tag, requeue=False) 
def start_consumer():
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host="rabbitmq",
            credentials=pika.PlainCredentials("rabbit", "docker")
        )
    )
    channel = connection.channel()

    channel.exchange_declare(exchange="dlx", exchange_type="direct")
    channel.queue_declare(queue="wod_jobs-dead", durable=True)
    channel.queue_bind(exchange="dlx", queue="wod_jobs-dead", routing_key="wod_jobs-dead")

    
    arguments = {
        "x-dead-letter-exchange": "dlx",
        "x-dead-letter-routing-key": "wod_jobs-dead",
        "x-message-ttl": 60000  
    }
    channel.queue_declare(queue="wod_jobs", durable=True, arguments=arguments)

    channel.basic_consume(queue="wod_jobs", on_message_callback=on_message)
    print("Waiting for WOD jobs...")
    channel.start_consuming()

