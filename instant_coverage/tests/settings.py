import os

DEBUG = True

SECRET_KEY = 'not empty'
ROOT_URLCONF = 'instant_coverage.tests.urls'

PROJECT_DIR = os.path.realpath(os.path.join(__file__, '..'))

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(PROJECT_DIR, 'db'),
    }
}
