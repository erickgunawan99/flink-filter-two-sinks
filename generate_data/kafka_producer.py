import random
import time
from datetime import datetime, timedelta

from confluent_kafka import Producer
from faker import Faker
import orjson


# ---------- Config ----------
KAFKA_BROKER = "localhost:29092"  # adjust to your Kafka broker
TOPIC = "user_events"

EVENT_TYPES = ["liked", "viewed", "bookmarked", "commented"]

fake = Faker()


# ---------- Kafka Setup ----------
conf = {
    "bootstrap.servers": KAFKA_BROKER,
    "client.id": "user-activity-producer",
}
producer = Producer(conf)


# ---------- Serializer ----------
def to_json_bytes(obj) -> bytes:
    return orjson.dumps(obj)


# ---------- Data Generator ----------
def generate_event():
    # Generate a random user ID to serve as our partition key
    user_id = random.randint(1, 10)

    # random datetime up to "now"
    random_days = random.randint(0, 30)
    date = datetime.now() - timedelta(days=random_days)

    event = {
        "event_type": random.choice(EVENT_TYPES),
        "url": fake.url(),
    }

    return {
        "id": str(user_id),
        "date": int(date.timestamp() * 1000),  # Millisecond timestamp
        "event": event,
    }


# ---------- Delivery Callback ----------
def delivery_report(err, msg):
    if err is not None:
        print(f"❌ Delivery failed: {err}")
    else:
        print(f"✅ Delivered to {msg.topic()} [{msg.partition()}] with key '{msg.key().decode('utf-8')}'")


# ---------- Main Producer Loop ----------
if __name__ == "__main__":
    try:
        while True:
            record = generate_event()
            payload = to_json_bytes(record)
            
            # Extract the user ID to use as the message key
            record_key = record["id"]

            producer.produce(
                TOPIC,
                key=record_key.encode('utf-8'), # <-- Key is added here
                value=payload,
                callback=delivery_report
            )

            # Trigger delivery callbacks
            producer.poll(0)
            
            # Control the event rate to 1 event per second
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nStopping producer...")

    finally:
        # Wait for all messages in the producer queue to be delivered.
        print("Flushing messages...")
        producer.flush()