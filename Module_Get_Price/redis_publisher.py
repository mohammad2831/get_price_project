import os
import redis
import json

host = os.getenv('REDIS_HOST', 'localhost')
redis_publisher = redis.Redis(host=host, port=6379, db=0, decode_responses=True)

def publish_price_change(product_label, title_fa, old_buy, old_sell, new_buy, new_sell):
    message = {
        "event": "price_updated",
        "product": {
            "label": product_label,
            "title": title_fa,
            "old_buy": old_buy,
            "old_sell": old_sell,
            "new_buy": new_buy,
            "new_sell": new_sell
        }
    }
    redis_publisher.publish("price_updates", json.dumps(message, ensure_ascii=False))
    print(f"Published: {title_fa} → {new_buy}/{new_sell}")