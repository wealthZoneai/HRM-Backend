from .settings import *

# ---------------------------------------------------
# DEVELOPMENT SETTINGS ONLY
# ---------------------------------------------------

DEBUG = True

# Safe wildcard for development only
ALLOWED_HOSTS = ["*"]

# Allow all origins during development
CORS_ALLOW_ALL_ORIGINS = True

# Fix MEDIA_ROOT if it was broken in settings.py
MEDIA_ROOT = BASE_DIR / "media"

# Use sqlite3 for dev
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'hrm_dev',
        'USER': 'postgres',
        'PASSWORD': 'Dinesh@41216',
        'HOST': '192.168.1.59',
        'PORT': '5432',
    }
}
