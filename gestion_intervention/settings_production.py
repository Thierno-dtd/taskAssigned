"""
Configuration de production pour SEEG Intervention Django
"""

import os
from pathlib import Path
from .settings import *

# Security
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
SECRET_KEY = os.environ.get('SECRET_KEY', 'votre-cle-secrete-tres-longue-et-aleatoire-a-changer-en-production')
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'api.seeg.ga,localhost,127.0.0.1').split(',')

# Database - PostgreSQL
db_name = os.environ.get('DB_NAME', 'seeg')
db_user = os.environ.get('DB_USER', 'obrice')
db_password = os.environ.get('DB_PASSWORD', 'azerty')
db_host = os.environ.get('DB_HOST', 'localhost')
db_port = os.environ.get('DB_PORT', '5432')

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': db_name,
        'USER': db_user,
        'PASSWORD': db_password,
        'HOST': db_host,
        'PORT': db_port,
    }
}

# Static files - DocumentRoot Apache /var/www/html/seeg
STATIC_ROOT = os.environ.get('STATIC_ROOT', '/var/www/html/seeg/static')
MEDIA_ROOT = os.environ.get('MEDIA_ROOT', '/var/www/html/seeg/media')

# CORS Settings
cors_origins = os.environ.get('CORS_ALLOWED_ORIGINS', 'https://app.seeg.ga,https://admin.seeg.ga')
if cors_origins:
    CORS_ALLOWED_ORIGINS = cors_origins.split(',')

csrf_origins = os.environ.get('CSRF_TRUSTED_ORIGINS', 'https://api.seeg.ga')
if csrf_origins:
    CSRF_TRUSTED_ORIGINS = csrf_origins.split(',')

# Security headers
SECURE_SSL_REDIRECT = os.environ.get('SECURE_SSL_REDIRECT', 'True').lower() == 'true'
SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'True').lower() == 'true'
CSRF_COOKIE_SECURE = os.environ.get('CSRF_COOKIE_SECURE', 'True').lower() == 'true'
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Email configuration
EMAIL_BACKEND = os.environ.get('EMAIL_BACKEND', 'django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True').lower() == 'true'
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@seeg.ga')
