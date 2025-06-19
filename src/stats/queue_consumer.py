import os
import pika
import json
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
logging.getLogger("pika").setLevel(logging.WARNING)
from .stats_service import save_workout_stat


class StatsQueueConsumer:
    _instance = None
    _is_initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(StatsQueueConsumer, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._is_initialized:
            self.connection = None
            self.channel = None
            self.exchange_name = "workout.performed"
            self.queue_name = "stats_workout_performed_queue"
            self._is_initialized = True
            self.connect()
            logger.info("StatsQueueConsumer initialized and connected to RabbitMQ")

    def ensure_connection(self):
        if not self.connection or self.connection.is_closed:
            self.connect()

    def connect(self):
        """Establish connection to RabbitMQ server"""
        logger.debug("Attempting to connect to RabbitMQ")
        credentials = pika.PlainCredentials(
            username=os.getenv("RABBITMQ_DEFAULT_USER", "rabbit"),
            password=os.getenv("RABBITMQ_DEFAULT_PASS", "docker"),
        )
        parameters = pika.ConnectionParameters(
            host=os.getenv("RABBITMQ_HOST", "rabbitmq"),
            port=5672,
            credentials=credentials,
            heartbeat=600,
            blocked_connection_timeout=300,
        )
        self.connection = pika.BlockingConnection(parameters)
        self.channel = self.connection.channel()

    
        self.channel.exchange_declare(
            exchange="workout.performed", exchange_type="direct", durable=True
        )

    
        self.channel.queue_declare(
            queue=self.queue_name,
            durable=True,
            arguments={
            "x-message-ttl": 60000, 
            "x-max-length": 100,
            "x-dead-letter-exchange": "workout.performed",
            "x-dead-letter-routing-key": "stats_workout_performed_queue",
            },
        )

        self.channel.queue_bind(
        exchange="workout.performed",
        queue=self.queue_name,
        routing_key=self.queue_name,
        )

        logger.info(
            f"Successfully connected to RabbitMQ and declared queue '{self.queue_name}'"
        )


    def on_message(self, ch, method, properties, body):
        try:
            logger.info(f"Received workout.performed event: {body.decode()}")
            message = json.loads(body)
            save_workout_stat(message)
            logger.info(f"Workout stat saved for user: {message.get('email')}")
            logger.info("Workout stat saved successfully.")
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except json.JSONDecodeError:
            logger.error("Failed to decode JSON message")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        except Exception as e:
            logger.error(
                f"Unexpected error processing message: {str(e)}", exc_info=True
            )
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

    def start_consuming(self):
        try:
            self.ensure_connection()
            self.channel.basic_qos(prefetch_count=1)
            self.channel.basic_consume(
                queue=self.queue_name, on_message_callback=self.on_message
            )
            logger.info(f"Started consuming from queue '{self.queue_name}'")
            self.channel.start_consuming()
        except KeyboardInterrupt:
            logger.info("Shutdown signal received, stopping consumer...")
            self.stop()
        except Exception as e:
            logger.error(f"Consumer error: {str(e)}", exc_info=True)
            self.stop()

    def stop(self):
        try:
            if self.channel and self.channel.is_open:
                self.channel.stop_consuming()
                logger.info("Stopped consuming messages")
            if self.connection and not self.connection.is_closed:
                self.connection.close()
                logger.info("Closed RabbitMQ connection")
        except Exception as e:
            logger.error(f"Error stopping consumer: {str(e)}", exc_info=True)


def run_consumer():
    consumer = StatsQueueConsumer()
    logger.info("Starting stats queue consumer")
    consumer.start_consuming()
