import json
from .extensions import redis_conn

CACHE_PREFIX = "order:"
def _cache_key(order_id):
    return f"{CACHE_PREFIX}{order_id}"
def set_cached_order(order_id, order_dict):
    redis_conn.set(_cache_key(order_id), json.dumps(order_dict))
def get_cached_order(order_id):
    raw = redis_conn.get(_cache_key(order_id))
    if raw is None:
        return None
    return json.loads(raw)
def delete_cached_order(order_id):
    redis_conn.delete(_cache_key(order_id))
