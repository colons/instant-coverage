import sys
from typing import Any, cast
from unittest.result import TestResult, failfast

import django
from django.test import SimpleTestCase
from django.test.utils import setup_test_environment, teardown_test_environment
from django.views.generic import View

import mock
import six

from .. import InstantCoverageMixin, clear_url_caches

if sys.version_info >= (3, 6):
    from typing import List, Tuple, Type, TYPE_CHECKING  # noqa: F401
else:
    TYPE_CHECKING = False

if TYPE_CHECKING:
    from unittest import TestCase  # noqa: F401
    from ..type_utils import ERROR_TYPE  # noqa: F401
    from .. import InstantCoverageAPI  # noqa: F401


def mocked_patterns(patterns):  # type: (list) -> mock.mock._patch
    clear_url_caches()
    return mock.patch('instant_coverage.tests.urls.urlpatterns', patterns)


class PickyTestResult(TestResult):
    """
    A TestResult subclass that will retain just exceptions and messages from
    tests run, rather than storing an entire traceback.
    """

    picky_failures = None  # type: List[Tuple[TestCase, ERROR_TYPE]]

    def __init__(self):  # type: () -> None
        super(PickyTestResult, self).__init__()
        self.picky_failures = []

    @failfast
    def addFailure(self, test, err):  # type: (TestCase, ERROR_TYPE) -> None
        if self.picky_failures is None:
            self.picky_failures = []

        self.picky_failures.append((test, err))


def get_results_for(
    test_name, mixin=InstantCoverageMixin, **test_attributes
):  # type: (str, Type[InstantCoverageAPI], Any) -> PickyTestResult

    if TYPE_CHECKING:
        EverythingTest = mixin
    else:
        class EverythingTest(mixin, SimpleTestCase):
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
        cast(Any, test)._pre_setup()

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
