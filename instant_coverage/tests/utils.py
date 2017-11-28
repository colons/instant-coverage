from unittest.result import TestResult, failfast
from instant_coverage import clear_url_caches

from django.http import HttpResponse
from django.test import SimpleTestCase
from django.test.utils import setup_test_environment, teardown_test_environment
from django.views.generic import View

from mock import patch
import six


def mocked_patterns(patterns):
    clear_url_caches()
    return patch('instant_coverage.tests.urls.urlpatterns', patterns)


class PickyTestResult(TestResult):
    """
    A TestResult subclass that will retain just exceptions and messages from
    tests run, rather than storing an entire traceback.
    """

    @failfast
    def addFailure(self, test, err):
        self.failures.append((test, err))


def get_results_for(test_name, mixin=None, **test_attributes):
    from instant_coverage import InstantCoverageMixin

    if mixin is None:
        class EverythingTest(InstantCoverageMixin, SimpleTestCase):
            pass
    else:
        class EverythingTest(mixin, InstantCoverageMixin, SimpleTestCase):
            pass

    setup_test_environment()
    test = EverythingTest(test_name)

    for attribute, value in six.iteritems(test_attributes):
        setattr(test, attribute, value)

    result = PickyTestResult()

    if hasattr(test, '_pre_setup'):
        test._pre_setup()

    test.run(result)

    teardown_test_environment()

    if not result.errors == []:
        # there should only ever be failures; if there's an error we should
        # throw something useful
        raise Exception(result.errors[0][1])
    return result


class WorkingView(View):
    def get(self, request, *args, **kwargs):
        return HttpResponse()


class BrokenView(View):
    def get(self, request, *args, **kwargs):
        raise Exception('this view is broken')
