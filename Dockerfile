# Dockerfile
FROM python:3.12-slim

# تنظیم متغیرهای محیطی
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# نصب وابستگی‌های سیستم
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# تنظیم دایرکتوری کاری
WORKDIR /app

# کپی requirements و نصب پکیج‌ها
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# کپی کل پروژه
COPY . .

# جمع‌آوری استاتیک (در صورت نیاز)
# RUN python manage.py collectstatic --noinput

# اجرای دستور پیش‌فرض (بعداً در docker-compose تغییر می‌کند)
CMD ["gunicorn", "get_price_project.wsgi:application", "--bind", "0.0.0.0:8000"]