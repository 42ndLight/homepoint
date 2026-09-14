# base.py

from pathlib import Path
import os
import dj_database_url
from decouple import config, Csv

from dotenv import load_dotenv


# Load environment variables from .env file
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY")

ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS").split(",")
NGROK_URL = os.getenv('NGROK_URL')

MPESA_CONSUMER_KEY = os.getenv('MPESA_CONSUMER_KEY')
MPESA_CONSUMER_SECRET = os.getenv('MPESA_CONSUMER_SECRET')
MPESA_BASE_URL = os.getenv('MPESA_BASE_URL')
MPESA_SHORTCODE = os.getenv('MPESA_SHORTCODE')
MPESA_PASSKEY = os.getenv('MPESA_PASSKEY')


PAYSTACK_SECRET_KEY = os.getenv('PAYSTACK_SECRET_KEY')
PAYSTACK_PUBLIC_KEY = os.getenv('PAYSTACK_PUBLIC_KEY')

AT_USERNAME = os.getenv('AT_USERNAME', 'sandbox')
AT_API_KEY = os.getenv('AT_API_KEY')
# Optional registered Africa's Talking sender ID/short code shown to recipients.
AT_SENDER_ID = os.getenv('AT_SENDER_ID')

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'orders',
    'payments',
    'users',
    'products',
    'reports',
    'files',
    'rest_framework',
    'corsheaders',
    'rest_framework_simplejwt.token_blacklist',
    'silk',
    'drf_yasg',
    'storages',
    'django_celery_beat',
    'django_celery_results',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    "whitenoise.middleware.WhiteNoiseMiddleware",
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'silk.middleware.SilkyMiddleware',
]

ROOT_URLCONF = 'homepointBackend.urls'

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

WSGI_APPLICATION = 'homepointBackend.wsgi.application'

# Database
# https://docs.djangoproject.com/en/6.0/ref/settings/#databases
DATABASE_URL = os.getenv('DATABASE_URL')

if DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.config(default=os.environ.get('DATABASE_URL'), conn_max_age=600)
    }
else:
    # Fallback for local
    DATABASES = { 'default': {
        'ENGINE':'django.db.backends.{}'.format(
             os.getenv('DB_ENGINE', 'postgresql')
         ),
        'NAME': os.environ.get('DB_NAME'),
        'USER': os.environ.get('DB_USER'),
        'PASSWORD': os.environ.get('DB_PASSWORD'), 
        'HOST': os.environ.get('DB_HOST'), # 'DB_HOST', localhost
        'PORT': os.environ.get('DB_PORT'),
    } 
}


# Password validation
# https://docs.djangoproject.com/en/6.0/ref/settings/#auth-password-validators

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

AUTH_USER_MODEL = 'users.User'

AUTHENTICATION_BACKENDS = [
    'users.backends.EmailOrUsernameModelBackend', 
    'django.contrib.auth.backends.ModelBackend',
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',  # We override per-view
    ],
    'DEFAULT_PAGINATION_CLASS': 'homepointBackend.pagination.FlexiblePageNumberPagination',
    'PAGE_SIZE': 50,  # Mobile-friendly default; clients can request up to 200 via ?page_size=
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',      # Prevent abuse
        'user': '1000/day',
    },
    'DEFAULT_FILTER_BACKENDS': ['django_filters.rest_framework.DjangoFilterBackend'],
}

from datetime import timedelta
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),
    'REFRESH_TOKEN_LIFETIME': timedelta(hours=4),
    'AUTH_HEADER_TYPES': ('Bearer',),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'TOKEN_OBTAIN_SERIALIZER': 'users.serializers.CustomTokenObtainPairSerializer',
}

# Internationalization
# https://docs.djangoproject.com/en/6.0/topics/i18n/
LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Africa/Nairobi'

USE_I18N = True

USE_TZ = True



# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.0/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles_collected'

STATICFILES_DIRS = [
    BASE_DIR / 'static',  
]

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'



# Celery Configuration
# Broker/result backend (can be overridden via environment)
CELERY_BROKER_URL = os.environ.get('REDIS_URL')
# By default keep Redis as result backend for performance, but optionally
# use the Django DB (django-celery-results) for durable result storage.
USE_DB_FOR_CELERY_RESULTS = config('USE_DB_FOR_CELERY_RESULTS', default=False, cast=bool)
if USE_DB_FOR_CELERY_RESULTS:
    CELERY_RESULT_BACKEND = 'django-db'
else:
    CELERY_RESULT_BACKEND = os.environ.get('REDIS_URL')

CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

# Connection and retry tuning for more reliable operations in Docker
# Tune via env vars when necessary
CELERY_BROKER_POOL_LIMIT = int(os.environ.get('CELERY_BROKER_POOL_LIMIT', 10))
CELERY_BROKER_CONNECTION_TIMEOUT = int(os.environ.get('CELERY_BROKER_CONNECTION_TIMEOUT', 30))
CELERY_BROKER_HEARTBEAT = int(os.environ.get('CELERY_BROKER_HEARTBEAT', 15))
CELERY_BROKER_TRANSPORT_OPTIONS = {
    'visibility_timeout': int(os.environ.get('CELERY_VISIBILITY_TIMEOUT', 3600)),
}
# Result expiration (seconds) when using persistent backends (django-db or redis)
CELERY_RESULT_EXPIRES = int(os.environ.get('CELERY_RESULT_EXPIRES', 60*60*24))
# Control whether tasks persist results (set False for fire-and-forget tasks)
CELERY_TASK_IGNORE_RESULT = False

CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

CELERY_BEAT_SCHEDULE = {
    'keep-neon-alive': {
        'task': 'homepointBackend.files.tasks.keep_neon_alive',
        'schedule': 300.0,  # Every 5 minutes
    },
    # Add your other scheduled tasks here
}