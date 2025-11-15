# get_price_project/get_price_project/celery.py

from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from datetime import timedelta # برای زمان‌بندی دوره‌ای

# 1. تنظیم متغیر محیطی پیش‌فرض جنگو برای برنامه Celery.
# این خط ضروری است تا Celery بتواند تنظیمات جنگو را بارگذاری کند.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'get_price_project.settings') 

# 2. ایجاد نمونه برنامه Celery
# 'get_price_project' نام پروژه شماست.
app = Celery('get_price_project')

# 3. پیکربندی از طریق تنظیمات جنگو
# این خط باعث می‌شود Celery تمام تنظیمات خود را از settings.py شما (با پیشوند CELERY_) بخواند.
app.config_from_object('django.conf:settings', namespace='CELERY')

# 4. تنظیم دستی زمان‌بندی Celery Beat (در صورت عدم استفاده از django-celery-beat)
# اگر این تنظیمات را در settings.py قرار داده‌اید، این بخش اختیاری است و می‌توانید آن را حذف کنید.
app.conf.update(
    # واسط (Broker) و بک‌اند (Backend) برای Redis
    broker_url='redis://127.0.0.1:6379/0',
    result_backend='redis://127.0.0.1:6379/0',
    
    # تنظیمات سریال‌سازی
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    
    # منطقه زمانی
    timezone = 'Asia/Tehran',
    enable_utc = False, # تنظیمات منطقه زمانی محلی

    # تنظیم Celery Beat برای اجرای دوره‌ای
    beat_schedule = {
        'fetch_product_price_khkpour_5_secound': {
            # **نام تسک صحیح بر اساس اپلیکیشن شما**
            'task': 'Module_Get_Price.tasks.fetch_product_prices_khakpour',
            # اجرا هر 5 ثانیه یکبار
            'schedule': timedelta(seconds=7), 
            'args': (), # اگر تسک آرگومان ندارد
        }
    }
)

# 5. کشف خودکار تسک‌ها
# این خط تمام فایل‌های tasks.py را در برنامه‌های لیست شده در INSTALLED_APPS پیدا می‌کند.
app.autodiscover_tasks()