from setuptools import setup

setup(
    name='django-test-everything',
    version=__import__('test_everything').__version__,
    platforms=['any'],
    packages=['test_everything'],
    install_requires=['Django', 'django-extensions'],
)
