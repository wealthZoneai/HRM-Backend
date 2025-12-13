from .settings import *

DEBUG = True

ALLOWED_HOSTS = ["*"]

CORS_ALLOW_ALL_ORIGINS = True

MEDIA_ROOT = BASE_DIR / "media"


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'hrms_dev',
        'USER': 'postgres',
        'PASSWORD': 'Dinesh@41216',
        'HOST': '192.168.1.42',
        'PORT': '5432',
    }
}
