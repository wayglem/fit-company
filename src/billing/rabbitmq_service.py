import os
import pika
import json
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)
logging.getLogger("pika").setLevel(logging.WARNING)

class EventPublisher:
    _instance = None
    _is_initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EventPublisher, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._is_initialized:
            self.connection = None
            self.channel = None
            self._is_initialized = True

    def ensure_connection(self):
        if not self.connection or self.connection.is_closed:
            self.connect()

    def connect(self):
        logger.debug("Connecting to RabbitMQ for event publishing...")
        credentials = pika.PlainCredentials(
            username=os.getenv("RABBITMQ_DEFAULT_USER", "rabbit"),
            password=os.getenv("RABBITMQ_DEFAULT_PASS", "docker")
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
        logger.info("RabbitMQ event publisher connected.")

    def publish_event(self, event_name: str, data: Dict[str, Any]) -> bool:
        try:
            self.ensure_connection()

            logger.debug(f"Declaring fanout exchange '{event_name}'")
            self.channel.exchange_declare(exchange=event_name, exchange_type='fanout', durable=True)

            logger.debug(f"Publishing event to '{event_name}': {data}")
            self.channel.basic_publish(
                exchange=event_name,
                routing_key='',
                body=json.dumps(data),
                properties=pika.BasicProperties(delivery_mode=2)
            )
            logger.info(f"Event '{event_name}' published successfully.")
            return True
        except Exception as e:
            logger.error(f"Failed to publish event '{event_name}': {e}", exc_info=True)
            return False

    def close(self):
        if self.connection and not self.connection.is_closed:
            logger.info("Closing RabbitMQ event publisher connection")
            self.connection.close()

event_publisher = EventPublisher()
