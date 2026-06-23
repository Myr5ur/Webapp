import os
import redis
from rq import Queue

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379")
redis_conn = redis.from_url(REDIS_URL, protocol=2)
payment_queue = Queue("payments", connection=redis_conn)