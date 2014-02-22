from unittest.result import TestResult, failfast

from django.conf import settings
from django.test.utils import setup_test_environment
from django.views.generic import View


def get_urlpatterns_stupid():
    return settings.ROOT_URLCONF


class PickyTestResult(TestResult):
    """
    A TestResult subclass that will retain just exceptions and messages from
    tests run, rather than storing an entire traceback.
    """

    @failfast
    def addFailure(self, test, err):
        self.failures.append((test, err))


def get_results_for(test_name):
    from instant_coverage import TestCase as Everything

    setup_test_environment()
    test = Everything(test_name)
    result = PickyTestResult()
    test._pre_setup()
    test.run(result)
    if not result.errors == []:
        # there should only ever be failures; if there's an error we should
        # throw something useful
        raise Exception(result.errors[0][1])
    return result


class WorkingView(View):
    pass


class BrokenView(View):
    def get(self, request, *args, **kwargs):
        raise Exception('this view is broken')
