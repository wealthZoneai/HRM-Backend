from .settings import *

DEBUG = True

ALLOWED_HOSTS = ["*"]

CORS_ALLOW_ALL_ORIGINS = True

MEDIA_ROOT = BASE_DIR / "media"


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'test',
        'USER': 'postgres',
        'PASSWORD': 'Ajay@2002',
        'HOST': '192.168.1.6',
        'PORT': '5432',
    }
}
