![A roll of duct tape; the Instant Coverage logo][logo]
[logo]: http://colons.co/instant-coverage-small.png

[![Build Status][travis-status]][travis]
[travis-status]: https://travis-ci.org/colons/instant-coverage.png

# Instant Coverage

Your new Django site need tests. Nothing super fancy, just enough that you know
you've not forgotten to close some &lt;div&gt; somewhere and it's not going to
start 500ing next time you deploy. You *could* write unit tests, but those are
boring and your client sure as hell isn't going to pay for the time.

You've got five minutes, though.

## Features

- **Simple**
    - Iterates through a list of URLs and complains if any of them 500.
- **Magic**
    - Will loudly complain when there are views missing from the list of URLs
      to test.
- **Has what you need**
    - Comes with optional test mixins for checking links and validating JSON.
- **Extensible**
    - Easily add tests that will run against every view on your website. If you
      want tests for things like consistent capitalisation of a particular
      phrase or the universal inclusion of a particular meta tag, you can have
      them in minutes.
- **Portable**
    - [Tested][travis] on Python 2.7 and 3.4 and Django 1.4, 1.5 and 1.6.

# Usage

## Setup

### Install

`pip install django-instant-coverage`

### ‘Write’ your tests

You'll want a tests module somewhere. I keep mine in my `PROJECT_DIR`, because
it's testing the whole site and not just one app. Wherever you put it, it
should be named such that your test runner will find it (`tests.py` usually
works well) and should contain at least the following:

```python
from django.test import TestCase
from instant_coverage import InstantCoverageMixin

class EverythingTest(InstantCoverageMixin, TestCase):
    pass
```

With that in place, you should be able to run your tests with `python manage.py
test`. They'll fail, though. You'll get a list of URLs you've not told it to
test, looking something like this:

```
AssertionError: The following views are untested:

('^',) ^$ (index)
('^admin/',) ^$ (index)
('^admin/',) ^logout/$ (logout)
('^admin/',) ^password_change/$ (password_change)
[...]
```

It'll probably contain a bunch of URLs you don't want to test, though, like
those from the Django admin app. To quickly exclude entire URL includes, add
tuples like the ones shown in the failure you just got to your test's
`uncovered_includes` attribute:

```python
class EverythingTest(InstantCoverageMixin, TestCase):
    uncovered_includes = [
        ('^admin/',),
    ]
```

Add URLs that you *do* actually want to test to `covered_urls`, and add those
you *don't* to `uncovered_urls`. If you forget what's still missing, run the
tests again to get an audit of what's left.

```python
class EverythingTest(InstantCoverageMixin, TestCase):
    covered_urls = [
        '/',
        '/api/',
        '/0007C3F2760E0541/',
    ]

    uncovered_urls = [
        # requires stuff to be in the session
        '/upload/confirm/',
        '/shortlist-selection/',

        # only accepts POST
        '/shortlist-order/',
    ]
```

If you have views that you can't test without data present in the database,
[make a fixtures file][dumpdata] and [add it to your test class][fixtures].

[dumpdata]: https://docs.djangoproject.com/en/dev/ref/django-admin/#dumpdata-app-label-app-label-app-label-model
[fixtures]: https://docs.djangoproject.com/en/dev/topics/testing/tools/#django.test.TransactionTestCase.fixtures

### Test under different circumstances

If you want to test all the URLs you've listed under different circumstances
(for instance, when a user is logged in or when a different language has been
selected), create a subclass of your tests and override `setUp()`. For
instance, you might put the following below your `EverythingTest`:

```python
from django.contrib.auth import get_user_model

class LoggedInEverythingTest(EverythingTest):
    def setUp(self):
        super(LoggedInEverythingTest, self).setUp()
        user = get_user_model()(
            username='user',
            is_staff=True,
            is_superuser=True,
        )
        user.set_password('pass')
        user.save()
        self.assertTrue(self.client.login(username='user', password='pass'))
```

### Use the provided optional test mixins

Instant Coverage provides a number of optional test mixins that you may find
useful. Look in `instant_coverage/optional.py` for details. To use them, do
something like this:

```python
from instant_coverage import InstantCoverageMixin, optional

class EverythingTest(optional.ValidJSON, InstantCoverageMixin, TestCase):
    # covered_urls, etc...
```

### Write your own tests

`InstantCoverageMixin` provides a `instant_responses` method that returns a
dictionary of responses and exceptions, keyed by URL. Test methods you write
should iterate across that. Have a look in `instant_coverage/optional.py` for
some examples.

[travis]: https://travis-ci.org/colons/instant-coverage
