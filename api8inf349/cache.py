import os 
import json

import redis

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost")
r = redis.from_url(REDIS_URL, protocol=2)


def cache_order(order_id, order_dict):
    cle = f"order:{order_id}"
    r.set(cle, json.dumps(order_dict, default=str), ex=3600)

def get_cached_order(order_id):
    cle = f"order:{order_id}"
    valeur = r.get(cle)
    if valeur is None:
        return None
    return json.loads(valeur)