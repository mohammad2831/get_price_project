# get_price_project/get_price_project/celery.py

from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from datetime import timedelta  # برای زمان‌بندی دوره‌ای

# 1. تنظیم متغیر محیطی پیش‌فرض جنگو برای برنامه Celery.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'get_price_project.settings') 

# 2. ایجاد نمونه برنامه Celery
app = Celery('get_price_project')

# 3. پیکربندی از طریق تنظیمات جنگو (اولویت بالاتر)
app.config_from_object('django.conf:settings', namespace='CELERY')

# 4. تنظیم دستی (فقط بروکر و بک‌اند رو فیکس می‌کنیم — بقیه دست نخورده!)
app.conf.update(
    # ← فقط این دو خط تغییر کردن
    broker_url='redis://redis-celery:6379/0',        # قبلاً 127.0.0.1 بود
    result_backend='redis://redis-celery:6379/1',    # قبلاً 127.0.0.1 بود + دیتابیس 1 بهتره

    # بقیه دقیقاً مثل قبل — هیچ تغییری نکردن
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    
    timezone='Asia/Tehran',
    enable_utc=False,

    # تنظیمات بیت کاملاً دست نخورده باقی موند
    beat_schedule={
        'fetch_product_price_khkpour_5_secound': {
            'task': 'Module_Get_Price.tasks.fetch_product_prices_khakpour',
            'schedule': timedelta(seconds=7), 
            'args': (),
        }
    }
)

# 5. کشف خودکار تسک‌ها
app.autodiscover_tasks()