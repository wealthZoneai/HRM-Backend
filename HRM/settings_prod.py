# HRM/HRM/settings_prod.py
"""
Minimal production settings scaffold.
This file intentionally only overrides critical settings from settings.py
and expects environment variables to be set in the deployment environment.
Do NOT commit real secrets to source control.
"""

import os
from .settings import *  # import base settings
import dj_database_url

# SECRET_KEY: must be provided via env var in prod
SECRET_KEY = os.environ.get("SECRET_KEY", None)
if not SECRET_KEY:
    raise Exception(
        "SECRET_KEY not set. Set environment variable SECRET_KEY in production.")

# DEBUG: force False in prod
DEBUG = os.environ.get("DEBUG", "False") == "True"

# ALLOWED_HOSTS: provide comma-separated list via env
allowed = os.environ.get("ALLOWED_HOSTS", "")
if allowed:
    ALLOWED_HOSTS = [h.strip() for h in allowed.split(",") if h.strip()]
else:
    ALLOWED_HOSTS = []

# Database: use DATABASE_URL environment variable if provided
database_url = os.environ.get("DATABASE_URL", "")
if not database_url:
    raise Exception(
        "DATABASE_URL not set. Set DATABASE_URL environment variable for production.")

if database_url.startswith("sqlite"):
    DATABASES = {
        "default": dj_database_url.parse(database_url, conn_max_age=0, ssl_require=False)
    }
else:
    DATABASES = {
        "default": dj_database_url.parse(database_url, conn_max_age=600, ssl_require=True)
    }


# CORS
CORS_ALLOW_ALL_ORIGINS = False
cors_origins = os.environ.get("CORS_ALLOWED_ORIGINS", "")
if cors_origins:
    CORS_ALLOWED_ORIGINS = [o.strip()
                            for o in cors_origins.split(",") if o.strip()]
else:
    CORS_ALLOWED_ORIGINS = []

# Security headers
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
