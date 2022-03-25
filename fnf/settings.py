"""
Django settings for fnf project.

This is the development mode settings file in the default location.
"""

import os
import secrets
from pathlib import Path

_env = os.environ.get('DJANGO_ENVIRONMENT', 'dev').lower().strip()
if _env.startswith('prod'):
    print("Using PRODUCTION settings:", _env)
    import fnf.settings_prod as mode
else:
    print("Using DEVELOPMENT settings:", _env)
    import fnf.settings_dev as mode

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.0/howto/deployment/checklist/

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = mode.DEBUG

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = secrets.token_urlsafe(64)

ALLOWED_HOSTS = mode.ALLOWED_HOSTS

# Application definition

INSTALLED_APPS = [
    'signup.apps.SignupConfig',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
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

ROOT_URLCONF = 'fnf.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'fnf.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.0/ref/settings/#databases

DATABASES = mode.DATABASES

# Password validation
# https://docs.djangoproject.com/en/4.0/ref/settings/#auth-password-validators
AUTH_PASSWORD_VALIDATORS = mode.AUTH_PASSWORD_VALIDATORS

# Internationalization
# https://docs.djangoproject.com/en/4.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.0/howto/static-files/

STATIC_URL = 'static/'

STATICFILES_DIRS = [
    BASE_DIR / "static",
    ('js', BASE_DIR / 'dist'),
]

# Default primary key field type
# https://docs.djangoproject.com/en/4.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

COORDINATOR_STATIC_IMG_URL = 'https://storage.googleapis.com/rock-scanner-5666/Coordinator%20Pics/'
COORDINATOR_DEFAULT_IMG = COORDINATOR_STATIC_IMG_URL + 'gearhead.png'

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

LOGIN_REDIRECT_URL = "/"

EMAIL_BACKEND = mode.EMAIL_BACKEND
EMAIL_HOST=os.environ.get('DJANGO_EMAIL_HOST')
EMAIL_PORT=os.environ.get('DJANGO_EMAIL_PORT')
EMAIL_HOST_USER=os.environ.get('DJANGO_EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD=os.environ.get('DJANGO_EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL=os.environ.get('DJANGO_DEFAULT_FROM_EMAIL')
EMAIL_USE_TLS=True

CSRF_TRUSTED_ORIGINS = mode.CSRF_TRUSTED_ORIGINS
