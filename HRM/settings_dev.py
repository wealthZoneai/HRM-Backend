from .settings import *

DEBUG = True

ALLOWED_HOSTS = ["*"]

CORS_ALLOW_ALL_ORIGINS = True

CORS_ALLOW_CREDENTIALS = False

MEDIA_ROOT = BASE_DIR / "media"

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': 'second_phase',
#         'USER': 'postgres',
#         'PASSWORD': 'Dinesh@41216',
#         'HOST': '192.168.1.3',
#         'PORT': '5432',
#     }
# }
