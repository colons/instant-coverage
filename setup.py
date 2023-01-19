from setuptools import setup

with open('README.rst') as readme_file:
    README = readme_file.read()

setup(
    name='django-instant-coverage',
    description='Better-than-nothing testing for Django',
    url='https://github.com/colons/instant-coverage',
    author='colons',
    author_email='pypi@colons.co',
    version='1.2.1',
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
    extras_require={
        'linting': [
            'django-stubs',
            'flake8',
            'flake8-import-order',
            'mypy',
            'types-beautifulsoup4',
            'types-html5lib',
            'types-mock',
            'types-requests',
            'types-six',
            'typing-extensions',
        ],
        'testing': [
            'pyenchant',
            'pytest',
            'wcag_zoo>=0.2.0',
        ],
    },
    long_description=README,
    long_description_content_type='text/x-rst',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Topic :: Software Development :: Testing',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
    ],
)
