# Module_Get_Price/tasks.py

from celery import shared_task
# وارد کردن توابع مورد نیاز از ماژول‌های پروژه
# تمام importهای دیگر (مانند models، requests و ...) را که در ابتدا داشتید، حذف کنید
# اگر در این فایل فقط به تابع fetch_product_prices نیاز دارید، همین یک خط کافی است
from .get_data_khakpour import fetch_product_prices # مسیر وارد کردن تابع شما



@shared_task(name='Module_Get_Price.tasks.fetch_product_prices_khakpour')
def fetch_product_prices_khakpour(): # نام تابع را تغییر دهید
    """تسک Celery برای فراخوانی تابع fetch_product_prices"""
    print("Celery task: Starting price fetching...")
    result = fetch_product_prices()
    
    if result and result[0].get('status') == 'error':
        print(f"Error during price update: {result[0].get('message')}")
    else:
        print("Celery task: Price fetching completed.")
    
    return result