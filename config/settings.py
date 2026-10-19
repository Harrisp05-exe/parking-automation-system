import os
from pathlib import Path
from decimal import Decimal
import dj_database_url
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')
PRODUCTION = os.getenv('VERCEL') == '1' or os.getenv('DJANGO_DEBUG', '1') == '0'
DEBUG = not PRODUCTION
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'local-development-only-change-before-hosting')
KIOSK_API_KEY = os.getenv('KIOSK_API_KEY', 'local-kiosk-key')
if PRODUCTION and (len(SECRET_KEY) < 40 or KIOSK_API_KEY == 'local-kiosk-key' or len(KIOSK_API_KEY) < 32):
    raise ValueError('Set strong DJANGO_SECRET_KEY (40+ characters) and KIOSK_API_KEY (32+ characters).')
ALLOWED_HOSTS = [h.strip() for h in os.getenv('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1,testserver').split(',') if h.strip()]
for key in ('VERCEL_URL', 'VERCEL_PROJECT_PRODUCTION_URL'):
    if os.getenv(key):
        ALLOWED_HOSTS.append(os.environ[key])
CSRF_TRUSTED_ORIGINS = [s for s in os.getenv('CSRF_TRUSTED_ORIGINS', '').split(',') if s]
INSTALLED_APPS = ['django.contrib.contenttypes', 'django.contrib.staticfiles', 'parking']
MIDDLEWARE = ['django.middleware.security.SecurityMiddleware', 'whitenoise.middleware.WhiteNoiseMiddleware', 'django.middleware.common.CommonMiddleware', 'django.middleware.csrf.CsrfViewMiddleware', 'django.middleware.clickjacking.XFrameOptionsMiddleware']
ROOT_URLCONF = 'config.urls'
WSGI_APPLICATION = 'config.wsgi.application'
TEMPLATES = [{'BACKEND':'django.template.backends.django.DjangoTemplates','DIRS':[], 'APP_DIRS':True, 'OPTIONS':{'context_processors':['django.template.context_processors.request']}}]
if PRODUCTION and not os.getenv('DATABASE_URL', '').startswith(('postgres://', 'postgresql://')):
    raise ValueError('Production requires a PostgreSQL DATABASE_URL.')
DATABASES = {'default': dj_database_url.config(default='sqlite:///' + str(BASE_DIR / 'db.sqlite3'), conn_max_age=0, ssl_require=PRODUCTION)}
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
USE_TZ = True
TIME_ZONE = os.getenv('PARKING_TIME_ZONE', 'Asia/Kolkata')
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STORAGES = {'default': {'BACKEND':'django.core.files.storage.FileSystemStorage'}, 'staticfiles': {'BACKEND':'whitenoise.storage.CompressedManifestStaticFilesStorage'}}
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = PRODUCTION
CSRF_COOKIE_SECURE = PRODUCTION
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = 'no-referrer'
SECURE_HSTS_SECONDS = 31536000 if PRODUCTION else 0
PARKING_RATE = Decimal(os.getenv('PARKING_RATE', '50.00'))
PARKING_CURRENCY = os.getenv('PARKING_CURRENCY', 'INR')
if PARKING_RATE <= 0:
    raise ValueError('PARKING_RATE must be positive.')
