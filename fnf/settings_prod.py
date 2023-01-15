"""
Production mode settings. All envronment based. 
"""

import os 
from pathlib import Path 

BASE_DIR = Path(__file__).resolve().parent.parent

DEBUG = False

SECRET_KEY = os.environ['DJANGO_SECRET_KEY']
ALLOWED_HOSTS = [ '*' ]
DATABASES = {
    'default': {
        'ENGINE': 'djongo',
        'NAME': os.environ.get('DJANGO_DB_NAME'),
        'CLIENT': {
            'host': os.environ.get('DJANGO_DB_HOST'),
        }
    },
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
EMAIL_BACKEND = os.environ.get('DJANGO_EMAIL_BACKEND')
CSRF_TRUSTED_ORIGINS = os.environ.get('DJANGO_TRUSTED_ORIGIN').split(',')
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
