from django.conf.urls import patterns, include, url
from django.http import HttpResponse, Http404
from django.shortcuts import redirect
from django.test import TestCase
from django.test.utils import override_settings

from .utils import (
    WorkingView, BrokenView, get_results_for, PickyTestResult,
    FakeURLPatternsTestCase, mocked_patterns
)

from instant_coverage import (
    IGNORE_TUTORIAL, INSTANT_TRACEBACKS_TUTORIAL, InstantCoverageMixin
)


class FailuresTest(FakeURLPatternsTestCase):
    def test_no_errors_okay(self):
        with mocked_patterns(patterns(
            '',
            url(r'^$', WorkingView.as_view()),
        )):
            results = get_results_for('test_no_errors', covered_urls=['/'])
            self.assertEqual(results.failures, [])

    def test_errors_surfaced(self):
        with mocked_patterns(patterns(
            '',
            url(r'^$', BrokenView.as_view()),
        )):
            results = get_results_for('test_no_errors', covered_urls=['/'])
            self.assertEqual(
                results.failures[0][1][1].args[0],
                "The following errors were raised:\n\n"
                "/: this view is broken\n\n"
                + INSTANT_TRACEBACKS_TUTORIAL.format(name='EverythingTest')
            )

    def test_missing_nameless_urls_complained_about(self):
        with mocked_patterns(patterns(
            '',
            url(r'^tested-url/$', WorkingView.as_view()),
            url(r'^untested-url/$', WorkingView.as_view()),
        )):
            results = get_results_for('test_all_urls_accounted_for',
                                      covered_urls=['/tested-url/'])
            self.assertEqual(
                results.failures[0][1][1].args[0],
                "The following views are untested:\n\n"
                "() ^untested-url/$ (None)\n\n"
                + IGNORE_TUTORIAL.format(name='EverythingTest')
            )

    def test_non_list_urls(self):
        """
        Ensure you can use a tuple of URLs if you so desire.
        """

        with mocked_patterns(patterns(
            '',
            url(r'^$', BrokenView.as_view()),
            url(r'^untested/$', WorkingView.as_view()),
        )):
            self.assertEqual(
                get_results_for('test_no_errors',
                                covered_urls='/',).failures[0][1][1].args[0],
                "The following errors were raised:\n\n"
                "/: this view is broken\n\n"
                + INSTANT_TRACEBACKS_TUTORIAL.format(name='EverythingTest')
            )
            self.assertEqual(
                get_results_for('test_all_urls_accounted_for',
                                covered_urls='/',).failures[0][1][1].args[0],
                "The following views are untested:\n\n"
                "() ^untested/$ (None)\n\n"
                + IGNORE_TUTORIAL.format(name='EverythingTest')
            )

    def test_missing_named_urls_complained_about(self):
        with mocked_patterns(patterns(
            '',
            url(r'^tested-url/$', WorkingView.as_view()),
            url(r'^untested-url/$', WorkingView.as_view(), name='name'),
        )):
            results = get_results_for('test_all_urls_accounted_for',
                                      covered_urls=['/tested-url/'])
            self.assertEqual(
                results.failures[0][1][1].args[0],
                "The following views are untested:\n\n"
                "() ^untested-url/$ (name)\n\n"
                + IGNORE_TUTORIAL.format(name='EverythingTest')
            )

    def test_excepted_urls_not_complained_about(self):
        with mocked_patterns(patterns(
            '',
            url(r'^tested-url/$', WorkingView.as_view()),
            url(r'^untested-url/$', WorkingView.as_view()),
            url(r'^deliberately-untested-url/$', WorkingView.as_view()),
        )):
            results = get_results_for(
                'test_all_urls_accounted_for',
                covered_urls=['/tested-url/'],
                uncovered_urls=['/deliberately-untested-url/'])

            self.assertEqual(
                results.failures[0][1][1].args[0],
                "The following views are untested:\n\n"
                "() ^untested-url/$ (None)\n\n"
                + IGNORE_TUTORIAL.format(name='EverythingTest')
            )

    def test_excepted_urls_ignored(self):
        with mocked_patterns(patterns(
            '',
            url(r'^tested-url/$', WorkingView.as_view()),
            url(r'^deliberately-untested-url/$', BrokenView.as_view()),
        )), override_settings(
            COVERED_URLS=['/tested-url/'],
            UNCOVERED_URLS=['/deliberately-untested-url/'],
        ):
            results = get_results_for('test_no_errors')
            self.assertEqual(results.failures, [])

    def test_broken_url_in_include(self):
        incl = patterns(
            '',
            url(r'^broken-url/$', BrokenView.as_view()),
        )

        with mocked_patterns(patterns(
            '',
            url(r'^include/', include(incl)),
        )):
            results = get_results_for('test_no_errors',
                                      covered_urls=['/include/broken-url/'])
            self.assertEqual(
                results.failures[0][1][1].args[0],
                "The following errors were raised:\n\n"
                "/include/broken-url/: this view is broken\n\n"
                + INSTANT_TRACEBACKS_TUTORIAL.format(name='EverythingTest')
            )

    def test_missing_url_in_include(self):
        incl = patterns(
            '',
            url(r'^broken-url/$', BrokenView.as_view()),
        )

        with mocked_patterns(patterns(
            '',
            url(r'^include/', include(incl)),
        )), override_settings(
            COVERED_URLS=[],
        ):
            results = get_results_for('test_all_urls_accounted_for')
            self.assertEqual(
                results.failures[0][1][1].args[0],
                "The following views are untested:\n\n"
                "('^include/',) ^broken-url/$ (None)\n\n"
                + IGNORE_TUTORIAL.format(name='EverythingTest')
            )

    def test_uncovered_includes(self):
        incl = patterns(
            '',
            url(r'^broken-url/$', BrokenView.as_view()),
        )

        with mocked_patterns(patterns(
            '',
            url(r'^include/', include(incl)),
        )):
            for test in [
                'test_all_urls_accounted_for',
                'test_no_errors',
            ]:
                results = get_results_for(
                    test, covered_urls=[], uncovered_includes=[('^include/',)])
                self.assertEqual(results.failures, [])

    def test_all_views_actually_called(self):
        views_called = []

        def view_one(*args, **kwargs):
            views_called.append('view_one')
            return HttpResponse()

        def view_two(*args, **kwargs):
            views_called.append('view_two')
            return HttpResponse()

        def included_view(*args, **kwargs):
            views_called.append('included_view')
            return HttpResponse()

        incl = patterns(
            '',
            url(r'^included/$', included_view),
        )

        with mocked_patterns(patterns(
            '',
            url(r'^one/$', view_one),
            url(r'^two/$', view_two),
            url(r'^include/', include(incl)),
        )):
            results = get_results_for('test_no_errors', covered_urls=[
                '/one/', '/two/', '/include/included/',
            ])
            self.assertEqual(results.failures, [])
            self.assertEqual(views_called,
                             ['view_one', 'view_two', 'included_view'])

    def test_bad_status_codes_caught(self):
        def missing_view(*args, **kwargs):
            raise Http404

        with mocked_patterns(patterns(
            '',
            url(r'^working-url/$', WorkingView.as_view()),
            url(r'^404-url/$', missing_view),
        )):
            results = get_results_for('test_acceptable_status_codes',
                                      covered_urls=['/working-url/',
                                                    '/404-url/'])
            self.assertEqual(
                results.failures[0][1][1].args[0],
                "The following bad status codes were seen:\n\n"
                "/404-url/: 404"
            )

    def test_instant_tracebacks(self):
        with mocked_patterns(patterns(
            '',
            url(r'^$', BrokenView.as_view()),
        )):
            results = get_results_for('test_no_errors',
                                      covered_urls=['/'],
                                      instant_tracebacks=True)

            # This is difficult to properly test, as tracebacks will vary from
            # system to system, so we fudge a little.
            self.assertIn(
                'most recent call last',
                results.failures[0][1][1].args[0],
            )

    def test_views_only_called_once_per_class(self):
        calls = []

        def a(*args, **kwargs):
            calls.append('a')
            return HttpResponse()

        def b(*args, **kwargs):
            calls.append('b')
            return HttpResponse()

        with mocked_patterns(patterns(
            '',
            url(r'^a/$', a),
            url(r'^b/$', b),
        )):
            class TestA(InstantCoverageMixin, TestCase):
                covered_urls = ['/a/']

            class TestB(InstantCoverageMixin, TestCase):
                covered_urls = ['/b/']

            for method in ['test_no_errors', 'test_acceptable_status_codes']:
                for test in [TestA(method), TestB(method)]:
                    test._pre_setup()
                    result = PickyTestResult()
                    test.run(result)
                    self.assertEqual(result.failures, [])
                    self.assertEqual(result.errors, [])

            self.assertEqual(calls, ['a', 'b'])

    def test_redirects_not_followed_if_follow_redirects_false(self):
        calls = []

        def redir(*args, **kwargs):
            calls.append('redir')
            return redirect('/target/')

        def target(*args, **kwargs):
            calls.append('target')
            return HttpResponse('hihi')

        with mocked_patterns(patterns(
            '',
            url(r'^redir/$', redir),
            url(r'^target/$', target),
        )):
            get_results_for('test_no_errors', covered_urls=['/redir/'])
            self.assertEqual(calls, ['redir', 'target'])

            calls = []

            get_results_for('test_no_errors', covered_urls=['/redir/'],
                            follow_redirects=False)
            self.assertEqual(calls, ['redir'])
