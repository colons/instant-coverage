import sys
from unittest import TestCase
from unittest.result import TestResult, failfast

import django
from django.test import SimpleTestCase
from django.test.utils import setup_test_environment, teardown_test_environment
from django.views.generic import View

import mock
import six

from .. import clear_url_caches

if sys.version_info >= (3, 6):
    from typing import TYPE_CHECKING
    if TYPE_CHECKING:
        from .. import ERROR_TYPE


def mocked_patterns(patterns):  # type: (list) -> mock.mock._patch
    clear_url_caches()
    return mock.patch('instant_coverage.tests.urls.urlpatterns', patterns)


class PickyTestResult(TestResult):
    """
    A TestResult subclass that will retain just exceptions and messages from
    tests run, rather than storing an entire traceback.
    """

    picky_failures = None  # type: list[tuple[TestCase, ERROR_TYPE]]

    def __init__(self):  # type: () -> None
        super().__init__()
        self.picky_failures = []

    @failfast
    def addFailure(self, test, err):  # type: (TestCase, ERROR_TYPE) -> None
        if self.picky_failures is None:
            self.picky_failures = []

        self.picky_failures.append((test, err))


def get_results_for(test_name, mixin=None, **test_attributes) -> PickyTestResult:
    from instant_coverage import InstantCoverageMixin

    if mixin is None:
        class EverythingTest(InstantCoverageMixin, SimpleTestCase):
            pass
    else:
        class EverythingTest(mixin, InstantCoverageMixin, SimpleTestCase):
            pass

    try:
        setup_test_environment()
    except RuntimeError:
        # look, this is gross, but what we're doing here to make an in-test
        # fake test environment is pretty gross already, so let's just placate
        # django for now:
        teardown_test_environment()
        setup_test_environment()

    test = EverythingTest(test_name)

    for attribute, value in six.iteritems(test_attributes):
        setattr(test, attribute, value)

    result = PickyTestResult()

    if hasattr(test, '_pre_setup'):
        test._pre_setup()  # type: ignore

    test.run(result)

    if not result.errors == []:
        # there should only ever be failures; if there's an error we should
        # throw something useful
        raise Exception(result.errors[0][1])
    return result


class WorkingView(View):
    def get(self, request):  # type: (django.http.HttpRequest) -> django.http.HttpResponse
        return django.http.HttpResponse()


class BrokenView(View):
    def get(self, request):  # type: (django.http.HttpRequest) -> django.http.HttpResponse
        raise Exception('this view is broken')
