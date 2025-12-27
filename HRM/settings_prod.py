# HRM/HRM/settings_prod.py
"""
Production settings.
"""

import os
from .settings import *
from django.core.management.utils import get_random_secret_key
import dj_database_url


env_secret = os.environ.get("SECRET_KEY")
if env_secret:
    SECRET_KEY = env_secret
else:
    try:
        SECRET_KEY
    except NameError:
        SECRET_KEY = get_random_secret_key()


DEBUG = os.environ.get("DEBUG", "False") == "True"


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
    CORS_ALLOWED_ORIGINS = []


csrf_trusted = os.environ.get("CSRF_TRUSTED_ORIGINS", "")
if csrf_trusted:
    CSRF_TRUSTED_ORIGINS = [
        o.strip() for o in csrf_trusted.split(",") if o.strip()
    ]
else:
    CSRF_TRUSTED_ORIGINS = []


SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

SECURE_HSTS_SECONDS = int(os.environ.get("SECURE_HSTS_SECONDS", "0"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = os.environ.get(
    "SECURE_HSTS_INCLUDE_SUBDOMAINS", "False") == "True"
SECURE_HSTS_PRELOAD = os.environ.get("SECURE_HSTS_PRELOAD", "False") == "True"

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True


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
