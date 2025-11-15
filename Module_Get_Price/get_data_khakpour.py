import requests
from rest_framework import status
import redis
import json
from datetime import datetime
import re
#from GeneratePrice_Module.models import ProductPrice
#from GeneratePrice_Module.consumers import PriceConsumer
from asgiref.sync import async_to_sync
#from channels.layers import get_channel_layer


from django.core.cache import cache
from django.conf import settings

def get_khakpour_token() -> str | None:
    """
    توکن Khakpour را از ردیس می‌خواند و JWT خام را برمی‌گرداند.
    
    Returns:
        str: JWT خام (بدون کوتیشن و بک‌اسلش)
        None: اگر توکن وجود نداشته باشد یا منقضی شده باشد
    """
    raw_token = cache.get(settings.KHAKPOUR_TOKEN_CACHE_KEY)
    
    if not raw_token:
        print("Token not found in Redis or expired.")
        return None

    # اگر سریالایزر JSON استفاده شده، مقدار یک رشته JSON است: "\"eyJ...\""
    if isinstance(raw_token, str) and raw_token.startswith('"') and raw_token.endswith('"'):
        # حذف کوتیشن‌ها و آن اسکیپ‌ها
        clean_token = raw_token[1:-1]  # حذف " اول و آخر
        clean_token = clean_token.replace('\\"', '"')  # اگر بک‌اسلش داشت
    else:
        clean_token = raw_token

    print(f"Token fetched from Redis: {clean_token[:50]}...")
    return clean_token



token = get_khakpour_token()

if token:
    print("توکن آماده استفاده:", token)
    # مثلاً در هدر درخواست بعدی
    headers = {"Authorization": f"Bearer {token}"}
else:
    print("توکن وجود ندارد — باید دوباره لاگین کنید.")




def fetch_product_prices():
    # توکن رو از ردیس بخون
    token = get_khakpour_token()

    if not token:
        return {
            'status': 'error',
            'message': 'توکن در دسترس نیست. لطفاً ابتدا لاگین کنید.'
        }, status.HTTP_401_UNAUTHORIZED

    # کوکی رو با توکن واقعی بساز
    cookies = {
        "access_token_web": token
    }

    # بقیه هدرها همون قبلی
    headers = {
        "Host": "api.khakpourgold.com",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Cache-Control": "no-cache",
        "X-Verify": "964503326",
        "Origin": "https://panel.khakpourgold.com",
        "Connection": "keep-alive",
        "Referer": "https://panel.khakpourgold.com/",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site",
        "TE": "trailers",
    }

    url = "https://api.khakpourgold.com/products"

    try:
        response = requests.get(url, headers=headers, cookies=cookies, timeout=15)
    except requests.exceptions.RequestException as e:
        return {
            'status': 'error',
            'message': f'خطای شبکه: {e}'
        }, status.HTTP_503_SERVICE_UNAVAILABLE

    # بقیه کد دقیقاً همون قبلیه...
    if response.status_code == status.HTTP_401_UNAUTHORIZED:
        return {
            'status': 'error',
            'message': 'توکن نامعتبر است. لطفاً دوباره لاگین کنید.'
        }, status.HTTP_401_UNAUTHORIZED

    if response.status_code == status.HTTP_200_OK:
        data = response.json()
        categories = data.get('data', [])

        if not categories:
            return {
                'status': 'error',
                'message': 'فروشگاه در دسترس نیست'
            }, status.HTTP_404_NOT_FOUND

        result = []
        invalid_prices = []

        for category in categories:
            category_title = category.get('title', 'Unknown Category')
            products = []
            for product in category.get('products', []):
                buy_price = product.get('buy_price', 0)
                sell_price = product.get('sell_price', 0)

                if buy_price == -1 or sell_price == -1:
                    invalid_prices.append({
                        'category': category_title,
                        'product': product.get('title', 'Unknown Product'),
                        'buy_price': buy_price,
                        'sell_price': sell_price
                    })

                products.append({
                    'title': product.get('title', 'Unknown Product'),
                    'buy_price': buy_price,
                    'sell_price': sell_price
                })
            result.append({
                'category': category_title,
                'products': products
            })

        response_data = {'status': 'success', 'data': result}

        if invalid_prices:
            return {
                'status': 'warning',
                'message': 'برخی محصولات قیمت نامعتبر دارند (-1).',
                'invalid_products': invalid_prices,
                'data': result
            }, status.HTTP_206_PARTIAL_CONTENT

        return response_data, status.HTTP_200_OK

    else:
        return {
            'status': 'error',
            'message': f'دریافت داده ناموفق. کد وضعیت: {response.status_code}',
            'response_text': response.text[:500]
        }, status.HTTP_500_INTERNAL_SERVER_ERROR





'''
redis_client = redis.StrictRedis(
    host="localhost",  # یا سرور Redis
    port=6379,
    db=0,
    decode_responses=True
)
'''

'''

def update_prices():
    channel_layer = get_channel_layer()
    price_data = {
        'product_id': 1,
        'base_price': 1500.00 + (25 * 100)  # قیمت تصادفی برای تست
    }
    async_to_sync(channel_layer.group_send)(
        'prices_global',  # یا f'user_{user_id}' برای کاربر خاص
        {
            'type': 'price_update',
            'price_data': price_data
        }
    )



    
def save_prices_to_redis(data: dict):
    PRODUCT_KEYS = {
        "نقد فردا": "naghd-farda",
        "ربع 86": "robe-86",
        "نقد پسفردا": "naghd-pasfarda",
        "آبشده کارتخوان": "abshode-kart",
        "نیم سکه 86": "nim-86",
        "تمام سکه 86": "tamam-86"
    }
    PRODUCT_KEY_TO_CHOICE = {
        "naghd-farda": "1",
        "robe-86": "6",
        "naghd-pasfarda": "2",
        "abshode-kart": "3",
        "nim-86": "4",
        "tamam-86": "9"
    }
    print("Starting save_prices_to_redis")
    if not data.get("data"):
        print("No valid data to cache")
        return {"status": "error", "message": "No valid data to cache"}

    try:
        redis_client.ping()
        print("Connected to Redis")
    except redis.RedisError as e:
        print(f"Redis connection error: {e}")
        return {"status": "error", "message": f"Redis connection failed: {e}"}

    channel_layer = get_channel_layer()
    if channel_layer is None:
        print("Channel layer not available")
        return {"status": "error", "message": "Channel layer not available"}

    for category in data["data"]:
        for product in category.get("products", []):
            product_title_fa = product.get("title", "Unknown")
            buy_price = product.get("buy_price", 0)
            sell_price = product.get("sell_price", 0)
            label = PRODUCT_KEYS.get(product_title_fa)
            if not label:
                print(f"No matching label for product: {product_title_fa}")
                continue

            new_buy_str = str(buy_price)
            new_sell_str = str(sell_price)

            sell_key = f"{label}-sell"
            buy_key = f"{label}-buy"
            old_sell = redis_client.get(sell_key)
            old_buy = redis_client.get(buy_key)

            old_sell_price = None
            if old_sell:
               
                old_sell_price = old_sell.split(';')[0] if ';' in old_sell else old_sell

            old_buy_price = None
            if old_buy:
                old_buy_price = old_buy.split(';')[0] if ';' in old_buy else old_buy
            if new_sell_str != old_sell_price or new_buy_str != old_buy_price:
                print(f"Price changed for {label}. Updating...")

                now = datetime.now().strftime("%H:%M:%S")

                try:
                    redis_client.set(sell_key, f"{new_sell_str};{now}", ex=300)
                    redis_client.set(buy_key, f"{new_buy_str};{now}", ex=300)
                    print(f"Saving {label}-sell: {new_sell_str};{now}")
                    print(f"Saving {label}-buy: {new_buy_str};{now}")
                except redis.RedisError as e:
                    print(f"Error saving to Redis: {e}")
                    return {"status": "error", "message": f"Failed to save to Redis: {e}"}

                product_choice = PRODUCT_KEY_TO_CHOICE.get(label)
                if not product_choice:
                    print(f"No matching ProductPrice choice for label: {label}")
                    continue

                try:
                    product_price = ProductPrice.objects.get(product=product_choice)
                    product_price.base_price_sell = int(new_sell_str)
                    product_price.base_price_buy = int(new_buy_str)
                    product_price.is_exist = True
                    product_price.save()
                    print(f"Updated ProductPrice for {label}: sell={new_sell_str}, buy={new_buy_str}")
                except ProductPrice.DoesNotExist:
                    print(f"ProductPrice for {label} does not exist. Creating new entry.")
                    ProductPrice.objects.create(
                        product=product_choice,
                        base_price_sell=int(new_sell_str),
                        base_price_buy=int(new_buy_str),
                        is_exist=True
                    )
                except Exception as e:
                    print(f"Error updating ProductPrice for {label}: {e}")
                    return {"status": "error", "message": f"Failed to update ProductPrice: {e}"}

                price_data = {
                    'product_id': label,
                    'base_price_buy': new_buy_str,
                    'base_price_sell': new_sell_str,
                    'timestamp': now
                }
                send_test_message_to_websocket(4, price_data)

                try:
                    async_to_sync(channel_layer.group_send)(
                        'price_updates',
                        {'type': 'price_update', 'price_data': price_data}
                    )
                    print(f"Pushed price update for {label} to WebSocket")
                except Exception as e:
                    print(f"Error pushing to WebSocket: {e}")

            else:
                print(f"No price change for {label}. Skipping update.")

    return {"status": "success", "message": "Products cached in Redis and updated in ProductPrice"}

'''



def fetch_product_prices():
    #update_prices()

    # Your request details
    url = "https://api.khakpourgold.com/products"
    headers = {
        "Host": "api.khakpourgold.com",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Cache-Control": "no-cache",
        "X-Verify": "964503326",
        "Origin":"https://panel.khakpourgold.com",

        "Connection": "keep-alive",
        "Referer": "https://panel.khakpourgold.com/",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site",
        "TE": "trailers",
    }


    cookies = {"access_token_web":"eyJpdiI6IlY2NkVkOEE0TmxENk5zb2VBN3c0Vnc9PSIsInZhbHVlIjoiek9KRk9Ib1VadW5FdlVmdWpteWp3cFlOdktqVlhuUDdoUEY4aXpobk53YlBIeGRqMDhPS1FJbS96YlVnbHErMVJjM3FOenBJZlVUbWtFdzZucU5DVFo5c2ZWYmVjR2pHRkluRkRhMk0rYlprM3VvdFYwMHhDU2ZhcFNhUUpWU3p3RXh6dkVsODQyV0h5cWtNR2FpYUorWTdxSEVzd2hPV2RSdTkzQWxkZXl4SVZmdTdWTjRWbERIZ0x0QmJPSE1xb3Z4WVYxQTFVOWpoZTR3d3pUZ3I2allEVHRQV2FTZkV3STBabnJ1TUNuZTdPWERKZk1OcU82ZWpRNlA4MWtKdURhTnJseU9uekxSSkd6WGl5bURPK095dGdBUlZYekdpZFlpZytER0ovaWFaWDhYY0xGSEJOcGZ2andTMVRjdk8iLCJtYWMiOiJlNjk5NTU1OGU0MGUyM2Q1MGYxMWJlMTg2YTVkMzE0MTg3OTlmNjI1NDgyOTExZWE2MGQxNDYzODY4NjdjMzk5IiwidGFnIjoiIn0%3D"}
    try:
        response = requests.get(url, headers=headers, cookies=cookies)
    except requests.exceptions.RequestException as e:
        return {
            'status': 'error',
            'message': f'A network error occurred: {e}'
        }, status.HTTP_503_SERVICE_UNAVAILABLE

    if response.status_code == status.HTTP_401_UNAUTHORIZED:
        return {
            'status': 'error',
            'message': 'مشکلی پیش امده است'
        }, status.HTTP_401_UNAUTHORIZED

    if response.status_code == status.HTTP_200_OK:
        data = response.json()
        categories = data.get('data', [])

        if not categories:
            return {
                'status': 'error',
                'message': 'فروشگاه در دسترس نیست'
            }, status.HTTP_404_NOT_FOUND

        result = []
        invalid_prices = []




        for category in categories:
            category_title = category.get('title', 'Unknown Category')
            products = []
            for product in category.get('products', []):
                buy_price = product.get('buy_price', 0)
                sell_price = product.get('sell_price', 0)

                if buy_price == -1 or sell_price == -1:
                    invalid_prices.append({
                        'category': category_title,
                        'product': product.get('title', 'Unknown Product'),
                        'buy_price': buy_price,
                        'sell_price': sell_price
                    })

                products.append({
                    'title': product.get('title', 'Unknown Product'),
                    'buy_price': buy_price,
                    'sell_price': sell_price
                })
            result.append({
                'category': category_title,
                'products': products
            })

        # همیشه داده‌ها را به Redis ذخیره کن، حتی اگر قیمت‌های نامعتبر وجود داشته باشند
        response_data = {'status': 'success', 'data': result}
        #save_prices_to_redis(response_data)

        if invalid_prices:
            return {
                'status': 'warning',
                'message': 'Some products have invalid prices (-1).',
                'invalid_products': invalid_prices,
                'data': result
            }, status.HTTP_206_PARTIAL_CONTENT

        return {'status': 'success', 'data': result}, status.HTTP_200_OK

    else:
        return {
            'status': 'error',
            'message': f'Failed to get data. Status code: {response.status_code}',
            'response_text': response.text
        }, status.HTTP_500_INTERNAL_SERVER_ERROR



