import os
from setuptools import setup

os.environ.setdefault("DJANGO_SETTINGS_MODULE",
                      "instant_coverage.tests.settings")

setup(
    name='django-instant-coverage',
    version='0.0.0',
    platforms=['any'],
    packages=['instant_coverage'],
    install_requires=[
        'Django',
        'django-extensions',
        'mock',
    ],
    tests_require=['nose'],
    test_suite='nose.collector',
)
