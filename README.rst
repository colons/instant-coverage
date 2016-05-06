.. image:: http://colons.co/instant-coverage-small.png
   :alt: A roll of duct tape; the instant coverage logo

Instant Coverage |status|
=========================

.. |status| image:: https://travis-ci.org/colons/instant-coverage.svg
   :target: https://travis-ci.org/colons/instant-coverage

Your new Django site need tests. Nothing super fancy, just enough that you know
you've not forgotten to close some <div> somewhere and it's not going to start
500ing next time you deploy. You *could* write unit tests, but those are boring
and your client sure as hell isn't going to pay for the time.

You've got five minutes, though.

Features
--------

Simple
    Iterates through a list of URLs and complains if any of them 500.

Magic
    Will loudly complain when there are views missing from the list of URLs to
    test.

Has what you need
    Comes with `optional mixins`_ for checking links and validating HTML, JSON
    or, your spelling.

Extensible
    Easily add tests that will run against every view on your website. If you
    want tests for things like consistent capitalisation of a particular phrase
    or the universal inclusion of a particular meta tag, you can have them in
    minutes.

Portable
    Tested_ on Python 2.7, 3.3, 3.4, and 3.5 with Django versions 1.4 to 1.9,
    with `some exclusions`_.

.. _some exclusions: https://github.com/colons/instant-coverage/blob/master/.travis.yml
.. _tested: https://travis-ci.org/colons/instant-coverage

Changes
=======

Changes made in each release are listed in tags_ in this repository.

.. _tags: https://github.com/colons/instant-coverage/releases

Usage
=====

Install
-------

``pip install django-instant-coverage``

‘Write’ your tests
------------------

You'll want a tests module somewhere. I keep mine in my ``PROJECT_DIR``,
because it's testing the whole site and not just one app. Wherever you put it,
it should be named such that your test runner will find it (``tests.py``
usually works well) and should contain at least the following:

.. code-block:: python

   from django.test import TestCase
   from instant_coverage import InstantCoverageMixin

   class EverythingTest(InstantCoverageMixin, TestCase):
       pass

With that in place, you should be able to run your tests with ``python
manage.py test``. They'll fail, though. You'll get a list of URLs you've not
told it to test, looking something like this:

::

   AssertionError: The following views are untested:

   ('^',) ^$ (index)
   ('^admin/',) ^$ (index)
   ('^admin/',) ^logout/$ (logout)
   ('^admin/',) ^password_change/$ (password_change)
   [...]

It'll probably contain a bunch of URLs you don't want to test, though, like
those from the Django admin app. To quickly exclude entire URL includes, add
tuples like the ones shown in the failure you just got to your test's
``uncovered_includes`` attribute:

.. code-block:: python

   class EverythingTest(InstantCoverageMixin, TestCase):
       uncovered_includes = [
           ('^admin/',),
       ]

Add paths matching the URLs that you *do* actually want to test to
``covered_urls``, and add paths that match those you *don't* to
``uncovered_urls``. If you forget what's still missing, run the tests again to
get an audit of what's left.

.. code-block:: python

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

           # probably tested pretty thoroughly by the django project
           '/media/woof.jpg',
       ]

If you want to use ``reverse()`` rather than hard-code URLs or if you want to
test more than one path for a given URL, that is fully supported. Encouraged_,
even. It doesn't matter how you build it, as long as ``covered_urls`` is a
list.

.. _Encouraged: https://github.com/colons/musicfortheblind.co.uk/blob/master/mftb5/tests.py

If you have views that you can't test without data present in the database,
`make a fixtures file`_ and `add it to your test class`_.

.. _make a fixtures file: https://docs.djangoproject.com/en/dev/ref/django-admin/#dumpdata-app-label-app-label-app-label-model
.. _add it to your test class: https://docs.djangoproject.com/en/dev/topics/testing/tools/#django.test.TransactionTestCase.fixtures

Use the provided optional test mixins
-------------------------------------

By default, Instant Coverage will make sure none of your views raise unhandled
exceptions and all of them return status codes between 200 and 399. There's a
good chance at least some of the provided `optional mixins`_ will be
appropriate for your website, so be sure to have a look through them and see
what strikes your fancy. Use them like this:

.. code-block:: python

   from instant_coverage import InstantCoverageMixin, optional

   class EverythingTest(
       optional.Spelling, optional.ExternalLinks, optional.ValidHTML5,
       InstantCoverageMixin, TestCase
   ):
       # covered_urls, etc...

Write your own tests
--------------------

``InstantCoverageMixin`` provides an ``instant_responses`` method that returns
a dictionary of |responses|_ keyed by URL. Test methods you write should
iterate across that. Have a look at the `optional mixins`_ for some examples.

.. |responses| replace:: Django test client ``Response`` objects
.. _responses: https://docs.djangoproject.com/en/dev/topics/testing/tools/#django.test.Response
.. _optional mixins: https://github.com/colons/instant-coverage/blob/master/instant_coverage/optional.py

If you make any that you think might be useful to any other websites, even if a
minority, a pull request would be very much appreciated.

Test under different circumstances
----------------------------------

If you want to test all the URLs you've listed under different circumstances
(for instance, when a user is logged in or when a different language has been
selected), create a subclass of your tests and override ``setUp()``. For
instance, you might put the following below your ``EverythingTest``:

.. code-block:: python

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

Be aware that, by default, the test client will follow redirects. If you do not
want this, set the ``follow_redirects`` attribute of your tests to ``False``.
If you have more specific requirements, you may have to override the
``get_client_kwargs`` or ``attempt_to_get_internal_url`` methods of your test.

If you have a bunch of test classes that test the same collection of URLs, you
may want to consider inheriting from ``InstantCoverageAPI`` instead of
``InstantCoverageMixin``; the former will not run any tests that you don't
explicitly add yourself.
