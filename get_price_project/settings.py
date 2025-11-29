from datetime import timedelta
from pathlib import Path
import os
BASE_DIR = Path(__file__).resolve().parent.parent
import redis

SECRET_KEY = 'django-insecure-i)g^f=tb=)q8$@qx4q7!iaoe5-$l&+x&&(xd#^*h82m4c#5*do'
DEBUG = True

ALLOWED_HOSTS = ['app-rxg.ir', "www.app-rxg.ir", 'localhost','127.0.0.1','185.10.75.158', '94.182.155.166']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'drf_spectacular', # اضافه کردن drf-spectacular

    'rest_framework',
    'drf_yasg',



    'Module_Get_Price',
    'django_celery_beat',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'get_price_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'get_price_project.wsgi.application'



DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}



AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]



LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True











REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}










# ──────────────────────────────────────────────────────────────
# ۱. کش جنگو + توکن‌ها → فقط redis-cache
# ──────────────────────────────────────────────────────────────
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://redis-cache:6379/0",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
        "KEY_PREFIX": "getprice",
    }
}

# ──────────────────────────────────────────────────────────────
# ۲. سلری و بیت → فقط redis-celery
# ──────────────────────────────────────────────────────────────
CELERY_BROKER_URL = "redis://redis-celery:6379/0"
CELERY_RESULT_BACKEND = "redis://redis-celery:6379/1"
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = "Asia/Tehran"
CELERY_ENABLE_UTC = False

# ──────────────────────────────────────────────────────────────
# ۳. اتصال مستقیم به redis-price برای قیمت + pub/sub
# ──────────────────────────────────────────────────────────────
REDIS_PRICE = redis.Redis(
    host='redis-price',
    port=6379,
    db=0,
    password=None,
    decode_responses=True,
    socket_keepalive=True,
    retry_on_timeout=True,
    health_check_interval=30,
)

# اسم چنل pub/sub (ثابت باشه برای همه پروژه‌ها)
CHANNEL_PRICE_LIVE = "prices:livedata"

# ──────────────────────────────────────────────────────────────
# ۴. کش توکن خاکپور (از redis-cache خونده میشه)
# ──────────────────────────────────────────────────────────────
KHAKPOUR_TOKEN_CACHE_KEY = 'KhakpourToken'
KHAKPOUR_TOKEN_EXPIRY = 4 * 24 * 60 * 60  # ۴ روز




























STATIC_URL = 'static/'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
