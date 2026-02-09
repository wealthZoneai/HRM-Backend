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
