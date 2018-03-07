import os
from setuptools import setup

os.environ.setdefault('DJANGO_SETTINGS_MODULE',
                      'instant_coverage.tests.settings')

with open('README.rst') as readme_file:
    README = readme_file.read()

setup(
    name='django-instant-coverage',
    description='Better-than-nothing testing for Django',
    url='https://github.com/colons/instant-coverage',
    author='colons',
    author_email='pypi@colons.co',
    version='1.1.0',
    license='BSD',
    platforms=['any'],
    packages=['instant_coverage'],
    install_requires=[
        'Django',
        'mock',
        'six',
        'beautifulsoup4',
        'requests',
        'html5lib',
    ],
    tests_require=[
        'nose',
        'pyenchant',
        'wcag_zoo>=0.2.0',
    ],
    test_suite='nose.collector',
    long_description=README,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Topic :: Software Development :: Testing',
    ],
)
