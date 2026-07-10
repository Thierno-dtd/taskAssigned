"""
Configuration de production pour SEEG Intervention Django.

Toutes les valeurs viennent du .env (via python-decouple, cohérent avec
settings.py) — plus aucun identifiant en dur dans le code source. Les
secrets (SECRET_KEY, DB_PASSWORD...) n'ont AUCUNE valeur par défaut ici :
le démarrage plante volontairement si le .env de prod est incomplet,
plutôt que de retomber silencieusement sur un identifiant faible connu
de tous ceux qui ont lu ce fichier sur GitHub.
"""

from decouple import config, Csv
from .settings import *

# Security
DEBUG = config('DEBUG', default=False, cast=bool)
SECRET_KEY = config('SECRET_KEY')  # pas de défaut : obligatoire en prod
ALLOWED_HOSTS = config('ALLOWED_HOSTS', cast=Csv())  # pas de défaut : obligatoire

# Database - PostgreSQL (aucun identifiant par défaut, doit venir du .env)
# sslmode='require' par défaut : les Postgres managés modernes (Neon,
# Render, Supabase...) exigent TLS. Mettre DB_SSLMODE=disable seulement
# pour une base Postgres locale sans TLS configuré.
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
        'OPTIONS': {'sslmode': config('DB_SSLMODE', default='require')},
    }
}

# Static/media files : STATIC_ROOT a un défaut universel dans settings.py
# de base (BASE_DIR/staticfiles), servi par WhiteNoise — fonctionne aussi
# bien sur Render que derrière Apache (deploy/debian13). Surchargez
# STATIC_ROOT/MEDIA_ROOT via .env uniquement si vous avez un besoin
# spécifique (ex: DocumentRoot Apache dédié).
MEDIA_ROOT = config('MEDIA_ROOT', default=str(BASE_DIR / 'media'))

# CORS / CSRF : pas de défaut = obligatoire en prod (le domaine du front
# React et de l'API doivent être explicitement déclarés, jamais devinés)
CORS_ALLOWED_ORIGINS = config('CORS_ALLOWED_ORIGINS', cast=Csv())
CSRF_TRUSTED_ORIGINS = config('CSRF_TRUSTED_ORIGINS', cast=Csv())

# Security headers
SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=True, cast=bool)
SESSION_COOKIE_SECURE = config('SESSION_COOKIE_SECURE', default=True, cast=bool)
CSRF_COOKIE_SECURE = config('CSRF_COOKIE_SECURE', default=True, cast=bool)
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@seeg.ga')