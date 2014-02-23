from django.conf.urls import patterns, include, url
from django.http import HttpResponse, Http404
from django.test import SimpleTestCase
from django.test.utils import override_settings

from .utils import (
    WorkingView, BrokenView, get_results_for, get_urlpatterns_stupid,
)

from instant_coverage import (
    IGNORE_TUTORIAL, INSTANT_TRACEBACKS_TUTORIAL
)

from mock import patch


class FailuresTest(SimpleTestCase):
    def run(self, *args, **kwargs):
        with patch('instant_coverage.get_urlpatterns', get_urlpatterns_stupid):
            super(FailuresTest, self).run(*args, **kwargs)

    def test_no_errors_okay(self):
        with override_settings(
            ROOT_URLCONF=patterns(
                '',
                url(r'^$', WorkingView.as_view()),
            ),
            COVERED_URLS=['/'],
        ):
            results = get_results_for('test_no_errors')
            self.assertEqual(results.failures, [])

    def test_errors_surfaced(self):
        with override_settings(
            ROOT_URLCONF=patterns(
                '',
                url(r'^$', BrokenView.as_view()),
            ),
            COVERED_URLS=['/'],
        ):
            results = get_results_for('test_no_errors')
            self.assertEqual(
                results.failures[0][1][1][0],
                "The following errors were raised:\n\n"
                "/: this view is broken\n\n"
                + INSTANT_TRACEBACKS_TUTORIAL
            )

    def test_missing_nameless_urls_complained_about(self):
        with override_settings(
            ROOT_URLCONF=patterns(
                '',
                url(r'^tested-url/$', WorkingView.as_view()),
                url(r'^untested-url/$', WorkingView.as_view()),
            ),
            COVERED_URLS=['/tested-url/'],
        ):
            results = get_results_for('test_all_urls_accounted_for')
            self.assertEqual(
                results.failures[0][1][1][0],
                "The following views are untested:\n\n"
                "() ^untested-url/$ (None)\n\n"
                + IGNORE_TUTORIAL
            )

    def test_missing_named_urls_complained_about(self):
        with override_settings(
            ROOT_URLCONF=patterns(
                '',
                url(r'^tested-url/$', WorkingView.as_view()),
                url(r'^untested-url/$', WorkingView.as_view(), name='name'),
            ),
            COVERED_URLS=['/tested-url/'],
        ):
            results = get_results_for('test_all_urls_accounted_for')
            self.assertEqual(
                results.failures[0][1][1][0],
                "The following views are untested:\n\n"
                "() ^untested-url/$ (name)\n\n"
                + IGNORE_TUTORIAL
            )

    def test_excepted_urls_not_complained_about(self):
        with override_settings(
            ROOT_URLCONF=patterns(
                '',
                url(r'^tested-url/$', WorkingView.as_view()),
                url(r'^untested-url/$', WorkingView.as_view()),
                url(r'^deliberately-untested-url/$', WorkingView.as_view()),
            ),
            COVERED_URLS=['/tested-url/'],
            UNCOVERED_URLS=['/deliberately-untested-url/'],
        ):
            results = get_results_for('test_all_urls_accounted_for')
            self.assertEqual(
                results.failures[0][1][1][0],
                "The following views are untested:\n\n"
                "() ^untested-url/$ (None)\n\n"
                + IGNORE_TUTORIAL
            )

    def test_excepted_urls_ignored(self):
        with override_settings(
            ROOT_URLCONF=patterns(
                '',
                url(r'^tested-url/$', WorkingView.as_view()),
                url(r'^deliberately-untested-url/$', BrokenView.as_view()),
            ),
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

        with override_settings(
            ROOT_URLCONF=patterns(
                '',
                url(r'^include/', include(incl)),
            ),
            COVERED_URLS=['/include/broken-url/'],
        ):
            results = get_results_for('test_no_errors')
            self.assertEqual(
                results.failures[0][1][1][0],
                "The following errors were raised:\n\n"
                "/include/broken-url/: this view is broken\n\n"
                + INSTANT_TRACEBACKS_TUTORIAL
            )

    def test_missing_url_in_include(self):
        incl = patterns(
            '',
            url(r'^broken-url/$', BrokenView.as_view()),
        )

        with override_settings(
            ROOT_URLCONF=patterns(
                '',
                url(r'^include/', include(incl)),
            ),
            COVERED_URLS=[],
        ):
            results = get_results_for('test_all_urls_accounted_for')
            self.assertEqual(
                results.failures[0][1][1][0],
                "The following views are untested:\n\n"
                "('^include/',) ^broken-url/$ (None)\n\n"
                + IGNORE_TUTORIAL
            )

    def test_uncovered_includes(self):
        incl = patterns(
            '',
            url(r'^broken-url/$', BrokenView.as_view()),
        )

        with override_settings(
            ROOT_URLCONF=patterns(
                '',
                url(r'^include/', include(incl)),
            ),
            COVERED_URLS=[],
            UNCOVERED_INCLUDES=[('^include/',)],
        ):
            for test in [
                'test_all_urls_accounted_for',
                'test_no_errors',
            ]:
                results = get_results_for(test)
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

        with override_settings(
            ROOT_URLCONF=patterns(
                '',
                url(r'^one/$', view_one),
                url(r'^two/$', view_two),
                url(r'^include/', include(incl)),
            ),
            COVERED_URLS=['/one/', '/two/', '/include/included/'],
        ):
            results = get_results_for('test_no_errors')
            self.assertEqual(results.failures, [])
            self.assertEqual(views_called,
                             ['view_one', 'view_two', 'included_view'])

    def test_bad_status_codes_caught(self):
        def missing_view(*args, **kwargs):
            raise Http404

        with override_settings(
            ROOT_URLCONF=patterns(
                '',
                url(r'^working-url/$', WorkingView.as_view()),
                url(r'^404-url/$', missing_view),
            ),
            COVERED_URLS=['/working-url/', '/404-url/'],
        ):
            results = get_results_for('test_acceptable_response_codes')
            self.assertEqual(
                results.failures[0][1][1][0],
                "The following bad status codes were seen:\n\n"
                "/404-url/: 404"
            )

    def test_instant_tracebacks(self):
        with override_settings(
            ROOT_URLCONF=patterns(
                '',
                url(r'^$', BrokenView.as_view()),
            ),
            COVERED_URLS=['/'],
            INSTANT_TRACEBACKS=True,
        ):
            results = get_results_for('test_no_errors')

            # This is difficult to properly test, as tracebacks will vary from
            # system to system, so we fudge a little.
            self.assertIn(
                'most recent call last',
                results.failures[0][1][1][0],
            )
