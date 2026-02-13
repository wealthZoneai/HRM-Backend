# HRM/HRM/settings_prod.py
"""
Production settings.
"""

import os
from .settings import *
from django.core.management.utils import get_random_secret_key
import dj_database_url


SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY")


DEBUG = False


allowed = os.environ.get("ALLOWED_HOSTS", "")
if allowed:
    ALLOWED_HOSTS = [h.strip() for h in allowed.split(",") if h.strip()]
else:
    ALLOWED_HOSTS = ["localhost", "127.0.0.1"]


DATABASES = {
    "default": dj_database_url.config(
        default=os.environ.get("DATABASE_URL"),
        conn_max_age=600,
        ssl_require=True
    )
}

CORS_ALLOW_ALL_ORIGINS = False
cors_origins = os.environ.get("CORS_ALLOWED_ORIGINS", "")
if cors_origins:
    CORS_ALLOWED_ORIGINS = [
        o.strip() for o in cors_origins.split(",") if o.strip()
    ]
else:
    raise RuntimeError("CORS_ALLOWED_ORIGINS must be set in production")


csrf_trusted = os.environ.get("CSRF_TRUSTED_ORIGINS", "")
if csrf_trusted:
    CSRF_TRUSTED_ORIGINS = [
        o.strip() for o in csrf_trusted.split(",") if o.strip()
    ]
else:
    raise RuntimeError("CSRF_TRUSTED_ORIGINS must be set in production")


SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

SECURE_HSTS_SECONDS = int(os.environ.get("SECURE_HSTS_SECONDS", "31536000"))

SECURE_HSTS_INCLUDE_SUBDOMAINS = os.environ.get(
    "SECURE_HSTS_INCLUDE_SUBDOMAINS", "False") == "True"
SECURE_HSTS_PRELOAD = os.environ.get("SECURE_HSTS_PRELOAD", "False") == "True"

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

EMAIL_HOST = os.environ.get("EMAIL_HOST")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", 587))
EMAIL_USE_TLS = True

EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD")

DEFAULT_FROM_EMAIL = 'noreply@wealthzonegroupai.com'


LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {"class": "logging.StreamHandler"},
    },
    "root": {
        "handlers": ["console"],
        "level": os.environ.get("LOG_LEVEL", "INFO"),
    },
}
