import os
import random
import datetime
import json
import asyncio
import logging
from aiokafka import AIOKafkaProducer


class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime.datetime, datetime.date, datetime.time)):
            return obj.isoformat()
        elif isinstance(obj, datetime.timedelta):
            return (datetime.datetime.min + obj).time().isoformat()
        return json.JSONEncoder.default(self, obj)


producer = None
producer_lock = asyncio.Lock()


async def upload_to_ingest(json_: dict):
    global producer
    
    # Get configuration from environment variables
    bootstrap_servers = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
    topic = os.getenv('KAFKA_TOPIC', 'scrape_games')
    
    if not producer:
        async with producer_lock:
            if not producer:
                prod = AIOKafkaProducer(bootstrap_servers=bootstrap_servers)
                await prod.start()
                logging.info(f"Kafka producer started (broker: {bootstrap_servers}, topic: {topic})")
                producer = prod
    try:
        random_key = str(random.randint(0, 1000000))
        await producer.send(topic, key=random_key.encode(), value=json.dumps(json_, cls=DateTimeEncoder).encode())
    except Exception as e:
        logging.error(f"Error uploading to Kafka: {str(e)}")

