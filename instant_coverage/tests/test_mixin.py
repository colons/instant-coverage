import django
from django.conf.urls import include
from django.http import Http404, HttpResponse
from django.shortcuts import redirect
from django.test import TestCase
from django.test.utils import override_settings

from .utils import BrokenView, PickyTestResult, WorkingView, get_results_for, mocked_patterns
from .. import IGNORE_TUTORIAL, INSTANT_TRACEBACKS_TUTORIAL, InstantCoverageMixin

if django.VERSION > (3, 0):
    from django.urls import re_path
else:
    from django.conf.urls import url as re_path  # type: ignore


class FailuresTest(TestCase):
    def test_no_errors_okay(self):  # type: () -> None
        with mocked_patterns([
            re_path(r'^$', WorkingView.as_view()),
        ]):
            results = get_results_for('test_no_errors', covered_urls=['/'])
            self.assertEqual(results.picky_failures, [])

    def test_errors_surfaced(self):  # type: () -> None
        with mocked_patterns([
            re_path(r'^$', BrokenView.as_view()),
        ]):
            results = get_results_for('test_no_errors', covered_urls=['/'])
            assert results.picky_failures[0][1][1] is not None
            self.assertEqual(
                results.picky_failures[0][1][1].args[0],
                "The following errors were raised:\n\n"
                "/: this view is broken\n\n" +
                INSTANT_TRACEBACKS_TUTORIAL.format(name='EverythingTest')
            )

    def test_missing_nameless_urls_complained_about(self):  # type: () -> None
        with mocked_patterns([
            re_path(r'^tested-url/$', WorkingView.as_view()),
            re_path(r'^untested-url/$', WorkingView.as_view()),
        ]):
            results = get_results_for('test_all_urls_accounted_for', covered_urls=['/tested-url/'])
            assert results.picky_failures[0][1][1] is not None
            self.assertEqual(
                results.picky_failures[0][1][1].args[0],
                "The following views are untested:\n\n"
                "() ^untested-url/$ (None)\n\n" +
                IGNORE_TUTORIAL.format(name='EverythingTest')
            )

    def test_messaging_for_non_regex_patterns(self):  # type: () -> None
        if django.VERSION < (2, 0):
            self.skipTest('only works on django 2.0 or newer')

        from django.urls import path

        with mocked_patterns([
            path('tested-url/', WorkingView.as_view()),
            path('untested-url/', WorkingView.as_view()),
            re_path(r'^another-untested-url/$', WorkingView.as_view()),
        ]):
            results = get_results_for('test_all_urls_accounted_for', covered_urls=['/tested-url/'])
            assert results.picky_failures[0][1][1] is not None
            self.assertEqual(
                'The following views are untested:\n\n'
                '() untested-url/ (None)\n'
                '() ^another-untested-url/$ (None)\n\n{}'
                .format(IGNORE_TUTORIAL.format(name='EverythingTest')),
                results.picky_failures[0][1][1].args[0],
            )

    def test_non_list_urls(self):  # type: () -> None
        """
        Ensure you can use a tuple of URLs if you so desire.
        """

        with mocked_patterns([
            re_path(r'^$', BrokenView.as_view()),
            re_path(r'^untested/$', WorkingView.as_view()),
        ]):
            results = get_results_for('test_no_errors', covered_urls=('/',))
            assert results.picky_failures[0][1][1] is not None
            self.assertEqual(
                results.picky_failures[0][1][1].args[0],
                "The following errors were raised:\n\n"
                "/: this view is broken\n\n" +
                INSTANT_TRACEBACKS_TUTORIAL.format(name='EverythingTest')
            )

            results = get_results_for('test_all_urls_accounted_for', covered_urls=('/',))
            assert results.picky_failures[0][1][1] is not None
            self.assertEqual(
                results.picky_failures[0][1][1].args[0],
                "The following views are untested:\n\n"
                "() ^untested/$ (None)\n\n" +
                IGNORE_TUTORIAL.format(name='EverythingTest')
            )

    def test_missing_named_urls_complained_about(self):  # type: () -> None
        with mocked_patterns([
            re_path(r'^tested-url/$', WorkingView.as_view()),
            re_path(r'^untested-url/$', WorkingView.as_view(), name='name'),
        ]):
            results = get_results_for('test_all_urls_accounted_for', covered_urls=['/tested-url/'])
            assert results.picky_failures[0][1][1] is not None
            self.assertEqual(
                results.picky_failures[0][1][1].args[0],
                "The following views are untested:\n\n"
                "() ^untested-url/$ (name)\n\n" +
                IGNORE_TUTORIAL.format(name='EverythingTest')
            )

    def test_excepted_urls_not_complained_about(self):  # type: () -> None
        with mocked_patterns([
            re_path(r'^tested-url/$', WorkingView.as_view()),
            re_path(r'^untested-url/$', WorkingView.as_view()),
            re_path(r'^deliberately-untested-url/$', WorkingView.as_view()),
        ]):
            results = get_results_for(
                'test_all_urls_accounted_for',
                covered_urls=['/tested-url/'],
                uncovered_urls=['/deliberately-untested-url/'])
            assert results.picky_failures[0][1][1] is not None
            self.assertEqual(
                results.picky_failures[0][1][1].args[0],
                "The following views are untested:\n\n"
                "() ^untested-url/$ (None)\n\n" +
                IGNORE_TUTORIAL.format(name='EverythingTest')
            )

    def test_excepted_urls_ignored(self):  # type: () -> None
        with mocked_patterns([
            re_path(r'^tested-url/$', WorkingView.as_view()),
            re_path(r'^deliberately-untested-url/$', BrokenView.as_view()),
        ]), override_settings(
            COVERED_URLS=['/tested-url/'],
            UNCOVERED_URLS=['/deliberately-untested-url/'],
        ):
            results = get_results_for('test_no_errors')
            self.assertEqual(results.picky_failures, [])

    def test_broken_url_in_include(self):  # type: () -> None
        incl = [
            re_path(r'^broken-url/$', BrokenView.as_view()),
        ]

        with mocked_patterns([
            re_path(r'^include/', include(incl)),
        ]):
            results = get_results_for('test_no_errors', covered_urls=['/include/broken-url/'])
            assert results.picky_failures[0][1][1] is not None
            self.assertEqual(
                results.picky_failures[0][1][1].args[0],
                "The following errors were raised:\n\n"
                "/include/broken-url/: this view is broken\n\n" +
                INSTANT_TRACEBACKS_TUTORIAL.format(name='EverythingTest')
            )

    def test_missing_url_in_include(self):  # type: () -> None
        incl = [
            re_path(r'^broken-url/$', BrokenView.as_view()),
        ]

        with mocked_patterns([
            re_path(r'^include/', include(incl)),
        ]), override_settings(
            COVERED_URLS=[],
        ):
            results = get_results_for('test_all_urls_accounted_for')
            assert results.picky_failures[0][1][1] is not None
            self.assertEqual(
                results.picky_failures[0][1][1].args[0],
                "The following views are untested:\n\n"
                "('^include/',) ^broken-url/$ (None)\n\n" +
                IGNORE_TUTORIAL.format(name='EverythingTest')
            )

    def test_uncovered_includes(self):  # type: () -> None
        incl = [
            re_path(r'^broken-url/$', BrokenView.as_view()),
        ]

        with mocked_patterns([
            re_path(r'^include/', include(incl)),
        ]):
            for test in [
                'test_all_urls_accounted_for',
                'test_no_errors',
            ]:
                results = get_results_for(
                    test, covered_urls=[], uncovered_includes=[('^include/',)])
                self.assertEqual(results.picky_failures, [])

    def test_uncoverd_includes_with_common_nested_patterns(self):  # type: () -> None
        incl_a = [re_path(r'^a/$', BrokenView.as_view())]
        incl_b = [re_path(r'^b/$', BrokenView.as_view())]
        nest = [
            re_path(r'^nest/', include(incl_a)),
            re_path(r'^nest/', include(incl_b)),
        ]

        with mocked_patterns([
            re_path(r'^include/', include(nest)),
        ]):
            for test in [
                'test_all_urls_accounted_for',
                'test_no_errors',
            ]:
                results = get_results_for(
                    test, covered_urls=[], uncovered_includes=[
                        ('^include/', '^nest/')
                    ]
                )
                self.assertEqual(results.picky_failures, [])

    def test_all_views_actually_called(self):  # type: () -> None
        views_called = []

        def view_one(request):  # type: (django.http.HttpRequest) -> HttpResponse
            views_called.append('view_one')
            return HttpResponse()

        def view_two(request):  # type: (django.http.HttpRequest) -> HttpResponse
            views_called.append('view_two')
            return HttpResponse()

        def included_view(request):  # type: (django.http.HttpRequest) -> HttpResponse
            views_called.append('included_view')
            return HttpResponse()

        incl = [
            re_path(r'^included/$', included_view),
        ]

        with mocked_patterns([
            re_path(r'^one/$', view_one),
            re_path(r'^two/$', view_two),
            re_path(r'^include/', include(incl)),
        ]):
            results = get_results_for('test_no_errors', covered_urls=[
                '/one/', '/two/', '/include/included/',
            ])
            self.assertEqual(results.picky_failures, [])
            self.assertEqual(views_called,
                             ['view_one', 'view_two', 'included_view'])

    def test_bad_status_codes_caught(self):  # type: () -> None
        def missing_view(request):  # type: (django.http.HttpRequest) -> HttpResponse
            raise Http404

        with mocked_patterns([
            re_path(r'^working-url/$', WorkingView.as_view()),
            re_path(r'^404-url/$', missing_view),
        ]):
            results = get_results_for('test_acceptable_status_codes', covered_urls=['/working-url/', '/404-url/'])
            assert results.picky_failures[0][1][1] is not None
            self.assertEqual(
                results.picky_failures[0][1][1].args[0],
                "The following bad status codes were seen:\n\n"
                "/404-url/: 404"
            )

    def test_instant_tracebacks(self):  # type: () -> None
        with mocked_patterns([
            re_path(r'^$', BrokenView.as_view()),
        ]):
            results = get_results_for('test_no_errors', covered_urls=['/'], instant_tracebacks=True)
            assert results.picky_failures[0][1][1] is not None

            # This is difficult to properly test, as tracebacks will vary from
            # system to system, so we fudge a little.
            self.assertIn(
                'most recent call last',
                results.picky_failures[0][1][1].args[0],
            )

    def test_views_only_called_once_per_class(self):  # type: () -> None
        calls = []

        def a(request):  # type: (django.http.HttpRequest) -> django.http.HttpResponse
            calls.append('a')
            return HttpResponse()

        def b(request):  # type: (django.http.HttpRequest) -> django.http.HttpResponse
            calls.append('b')
            return HttpResponse()

        with mocked_patterns([
            re_path(r'^a/$', a),
            re_path(r'^b/$', b),
        ]):
            class TestA(InstantCoverageMixin, TestCase):
                covered_urls = ['/a/']

            class TestB(InstantCoverageMixin, TestCase):
                covered_urls = ['/b/']

            for method in ['test_no_errors', 'test_acceptable_status_codes']:
                for test in [TestA(method), TestB(method)]:
                    if hasattr(test, '_pre_setup'):
                        test._pre_setup()
                    result = PickyTestResult()
                    test.run(result)
                    self.assertEqual(result.picky_failures, [])
                    self.assertEqual(result.errors, [])

            self.assertEqual(calls, ['a', 'b'])

    def test_redirects_not_followed_if_follow_redirects_false(self):  # type: () -> None
        calls = []

        def redir(request):  # type: (django.http.HttpRequest) -> HttpResponse
            calls.append('redir')
            return redirect('/target/')

        def target(request):  # type: (django.http.HttpRequest) -> HttpResponse
            calls.append('target')
            return HttpResponse('hihi')

        with mocked_patterns([
            re_path(r'^redir/$', redir),
            re_path(r'^target/$', target),
        ]):
            get_results_for('test_no_errors', covered_urls=['/redir/'])
            self.assertEqual(calls, ['redir', 'target'])

            calls = []

            get_results_for('test_no_errors', covered_urls=['/redir/'],
                            follow_redirects=False)
            self.assertEqual(calls, ['redir'])
