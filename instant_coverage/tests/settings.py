import os

DEBUG = True

SECRET_KEY = 'not empty'

PROJECT_DIR = os.path.realpath(os.path.join(__file__, '..'))

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(PROJECT_DIR, 'db'),
    }
}
