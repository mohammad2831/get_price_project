import requests
from rest_framework import status
import redis
import json
from datetime import datetime
from asgiref.sync import async_to_sync
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
    redis_client = settings.REDIS_PRICE    # حتماً redis-price باشه!

    PRODUCT_KEYS = {
        "نقد فردا": "naghd-farda",
        "ربع 86": "robe-86",
        "نقد پسفردا": "naghd-pasfarda",
        "آبشده کارتخوان": "abshode-kart",
        "نیم سکه 86": "nim-86",
        "تمام سکه 86": "tamam-86"
    }

    if not data.get("data"):
        print("No valid data to save")
        return

    try:
        redis_client.ping()
    except Exception as e:
        print(f"Redis-Price connection error: {e}")
        return

    updated_count = 0

    for category in data["data"]:
        for product in category.get("products", []):
            title_fa = product.get("title", "").strip()
            buy_price = product.get("buy_price", 0)
            sell_price = product.get("sell_price", 0)

            label = PRODUCT_KEYS.get(title_fa)
            if not label:
                continue

            buy_key = f"{label}-buy"
            sell_key = f"{label}-sell"

            new_buy_str = str(buy_price)
            new_sell_str = str(sell_price)

            # فقط اگر تغییر کرد، publish کن و ذخیره کن
            old_buy = redis_client.get(buy_key)
            old_sell = redis_client.get(sell_key)

            if old_buy != new_buy_str or old_sell != new_sell_str:
                # ذخیره قیمت جدید (بدون TTL! چون همیشه آخرین مقدار مهمه)
                redis_client.set(buy_key, new_buy_str)      # ex=300 حذف شد
                redis_client.set(sell_key, new_sell_str)    # ex=300 حذف شد

                print(f"قیمت بروزرسانی شد → {title_fa}")
                print(f"   خرید: {old_buy} → {new_buy_str}")
                print(f"   فروش: {old_sell} → {new_sell_str}")

                # publish تغییر قیمت
                publish_price_change(
                    product_label=label,
                    title_fa=title_fa,
                    old_buy=old_buy,
                    old_sell=old_sell,
                    new_buy=new_buy_str,
                    new_sell=new_sell_str
                )
                updated_count += 1

    if updated_count == 0:
        print("هیچ قیمتی تغییر نکرد.")
    else:
        print(f"تعداد {updated_count} محصول بروزرسانی شد.")