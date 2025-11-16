import requests
from rest_framework import status
import redis
import json
from datetime import datetime
#import rek
#from GeneratePrice_Module.models import ProductPrice
#from GeneratePrice_Module.consumers import PriceConsumer
from asgiref.sync import async_to_sync
#from channels.layers import get_channel_layer

#from django_redis import get_redis_connectionk
from django.core.cache import cache
from django.conf import settings
from . redis_publisher import publish_price_change
from django_redis import get_redis_connection
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
    """
    دریافت لیست محصولات و قیمت‌ها از API خکپور.
    
    - توکن از ردیس خوانده می‌شود
    - همه محصولات (حتی با قیمت -1) نمایش داده می‌شوند
    - هیچ warning یا فیلتری وجود ندارد
    - خروجی: همیشه 200 OK (اگر API در دسترس باشد)
    
    Returns:
        tuple: (response_data, status_code)
    """
    # 1. دریافت توکن از ردیس
    token = get_khakpour_token()
    if not token:
        return {
            'status': 'error',
            'message': 'توکن احراز هویت یافت نشد. لطفاً ابتدا لاگین کنید.'
        }, status.HTTP_401_UNAUTHORIZED

    # 2. تنظیمات درخواست
    url = "https://api.khakpourgold.com/products"
    
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

    cookies = {
        "access_token_web": token
    }

    # 3. ارسال درخواست
    try:
        response = requests.get(
            url,
            headers=headers,
            cookies=cookies,
            timeout=15,
            verify=False  # فقط در توسعه! در production: verify=True
        )
    except requests.exceptions.RequestException as e:
        return {
            'status': 'error',
            'message': f'خطای ارتباط با سرور: {str(e)}'
        }, status.HTTP_503_SERVICE_UNAVAILABLE

    # 4. مدیریت وضعیت 401 (توکن نامعتبر)
    if response.status_code == status.HTTP_401_UNAUTHORIZED:
        return {
            'status': 'error',
            'message': 'توکن منقضی یا نامعتبر است. لطفاً دوباره لاگین کنید.'
        }, status.HTTP_401_UNAUTHORIZED

    # 5. اگر API در دسترس نیست
    if response.status_code != status.HTTP_200_OK:
        return {
            'status': 'error',
            'message': f'سرویس در دسترس نیست. کد وضعیت: {response.status_code}',
            'response_text': response.text[:500]
        }, status.HTTP_503_SERVICE_UNAVAILABLE

    # 6. پارس JSON
    try:
        data = response.json()
    except requests.exceptions.JSONDecodeError:
        return {
            'status': 'error',
            'message': 'پاسخ API معتبر نیست (JSON نامعتبر).'
        }, status.HTTP_502_BAD_GATEWAY

    # 7. استخراج دسته‌بندی‌ها
    categories = data.get('data', [])
    if not categories:
        return {
            'status': 'error',
            'message': 'هیچ دسته‌بندی محصولی یافت نشد.'
        }, status.HTTP_404_NOT_FOUND

    # 8. ساخت خروجی نهایی
    result = []
    for category in categories:
        category_title = category.get('title', 'دسته‌بندی نامشخص')
        products = []

        for product in category.get('products', []):
            products.append({
                'title': product.get('title', 'محصول نامشخص'),
                'buy_price': product.get('buy_price', 0),
                'sell_price': product.get('sell_price', 0),
            })

        result.append({
            'category': category_title,
            'products': products
        })
        print(result)
        save_prices_to_redis(data)
    # 9. خروجی موفق
    return {
        'status': 'success',
        'data': result
    }, status.HTTP_200_OK





def save_prices_to_redis(data: dict):
    redis_client = get_redis_connection("default")
    """
    ذخیره قیمت‌ها در ردیس فقط اگر تغییر کرده باشند.
    
    - مقایسه با مقدار قبلی
    - فقط تغییر → ذخیره + پیام
    - بدون وب‌سوکت، بدون دیتابیس
    """
    # نقشه نام فارسی → کلید کوتاه
    PRODUCT_KEYS = {
        "نقد فردا": "naghd-farda",
        "ربع 86": "robe-86",
        "نقد پسفردا": "naghd-pasfarda",
        "آبشده کارتخوان": "abshode-kart",
        "نیم سکه 86": "nim-86",
        "تمام سکه 86": "tamam-86"
    }

    # چک داده ورودی
    if not data.get("data"):
        print("No valid data to cache")
        return

    # اتصال به ردیس
    try:
        redis_client.ping()
        print("Connected to Redis")
    except Exception as e:
        print(f"Redis connection error: {e}")
        return

    updated = False  # آیا تغییری رخ داد؟

    for category in data["data"]:
        for product in category.get("products", []):
            title_fa = product.get("title", "").strip()
            buy_price = product.get("buy_price", 0)
            sell_price = product.get("sell_price", 0)

            # پیدا کردن لیبل
            label = PRODUCT_KEYS.get(title_fa)
            if not label:
                continue  # محصول ناشناخته

            # کلیدهای ردیس
            buy_key = f"{label}-buy"
            sell_key = f"{label}-sell"

            # خواندن قیمت قبلی
            old_buy = redis_client.get(buy_key)
            old_sell = redis_client.get(sell_key)

            old_buy_val = old_buy.decode('utf-8') if old_buy else None
            old_sell_val = old_sell.decode('utf-8') if old_sell else None

            new_buy_str = str(buy_price)
            new_sell_str = str(sell_price)

            # مقایسه
            if new_buy_str != old_buy_val or new_sell_str != old_sell_val:
                # تغییر کرد → ذخیره
                try:
                    redis_client.set(buy_key, new_buy_str, ex=300)  # 5 دقیقه
                    redis_client.set(sell_key, new_sell_str, ex=300)
                    
                    print(f"قیمت تغییر کرد → {title_fa}")
                    print(f"   خرید: {old_buy_val or '-'} → {new_buy_str}")
                    print(f"   فروش: {old_sell_val or '-'} → {new_sell_str}")
                    print(f"   کلیدها: {buy_key}, {sell_key}")
                    print("-" * 50)

                    publish_price_change(
                        product_label=label,
                        title_fa=title_fa,
                        old_buy=old_buy_val,
                        old_sell=old_sell_val,
                        new_buy=new_buy_str,
                        new_sell=new_sell_str
                    )
                    
                    updated = True
                except Exception as e:
                    print(f"خطا در ذخیره در ردیس: {e}")
            # else: تغییری نکرد → هیچی

    if not updated:
        print("هیچ قیمتی تغییر نکرده است.")


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

'''


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

'''
