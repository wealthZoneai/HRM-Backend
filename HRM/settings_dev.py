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

<<<<<<< Updated upstream
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
=======
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True

EMAIL_HOST_USER = 'nagirikantiajay20@gmail.com'
EMAIL_HOST_PASSWORD = 'khfj qsft sjeb tvax'

DEFAULT_FROM_EMAIL = EMAIL_HOST_USER


# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': 'api_testing',
#         'USER': 'postgres',
#         'PASSWORD': 'Dinesh@41216',
#         'HOST': '192.168.1.24',
#         'PORT': '5432',
#     }
# }
>>>>>>> Stashed changes
