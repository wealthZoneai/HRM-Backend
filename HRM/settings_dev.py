
import django
from .settings import *

DEBUG = True

ALLOWED_HOSTS = ["*"]

CORS_ALLOW_ALL_ORIGINS = True

CORS_ALLOW_CREDENTIALS = False

MEDIA_ROOT = BASE_DIR / "media"


# # Use sqlite3 for dev
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': 'hrm_dev',
#         'USER': 'postgres',
#         'PASSWORD': 'Dinesh@41216',
#         'HOST': '192.168.1.59',
#         'PORT': '5432',
#     }
# }

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True

EMAIL_HOST_USER = 'nagirikantiajay20@gmail.com'
EMAIL_HOST_PASSWORD = 'khfj qsft sjeb tvax'

DEFAULT_FROM_EMAIL = EMAIL_HOST_USER



