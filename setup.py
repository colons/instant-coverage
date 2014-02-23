import os
from setuptools import setup

os.environ.setdefault("DJANGO_SETTINGS_MODULE",
                      "instant_coverage.tests.settings")

setup(
    name='django-instant-coverage',
    description='Better-than-nothing testing for Django',
    url='https://github.com/colons/instant-coverage',
    version='0.0.1',
    platforms=['any'],
    packages=['instant_coverage'],
    install_requires=[
        'Django',
        'mock',
        'beautifulsoup4',
        'requests',
    ],
    tests_require=['nose'],
    test_suite='nose.collector',
)
