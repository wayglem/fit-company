#!/usr/bin/env python
import threading
from src.stats.app import run_app
from src.stats.queue_consumer import run_consumer
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def start_consumer():
    """Start the queue consumer in a separate thread"""
    consumer_thread = threading.Thread(target=run_consumer, daemon=True)
    consumer_thread.start()


if __name__ == "__main__":
    logger.info("Booting up stats service")
    start_consumer()
    run_app()