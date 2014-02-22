from django.conf.urls import patterns
from django.test import SimpleTestCase
from django.test.utils import override_settings

from .utils import (
    WorkingView, BrokenView, get_results_for, get_urlpatterns_stupid,
)

from instant_coverage import url_with_url_sufacing_url_patterns as url

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
            INTERNAL_URLS=['/'],
        ):
            results = get_results_for('test_no_errors')
            self.assertEqual(results.failures, [])

    def test_errors_surfaced(self):
        with override_settings(
            ROOT_URLCONF=patterns(
                '',
                url(r'^$', BrokenView.as_view()),
            ),
            INTERNAL_URLS=['/'],
        ):
            results = get_results_for('test_no_errors')
            self.assertEqual(
                results.failures[0][1][1][0],
                "The following errors were raised:\n"
                "/: this view is broken"
            )

    def test_missing_nameless_urls_complained_about(self):
        with override_settings(
            ROOT_URLCONF=patterns(
                '',
                url(r'^tested-url/$', WorkingView.as_view()),
                url(r'^untested-url/$', WorkingView.as_view()),
            ),
            INTERNAL_URLS=['/tested-url/'],
        ):
            results = get_results_for('test_all_urls_accounted_for')
            self.assertEqual(
                results.failures[0][1][1][0],
                "The following views are untested:\n"
                "^untested-url/$ (None)"
            )

    def test_missing_named_urls_complained_about(self):
        with override_settings(
            ROOT_URLCONF=patterns(
                '',
                url(r'^tested-url/$', WorkingView.as_view()),
                url(r'^untested-url/$', WorkingView.as_view(), name='name'),
            ),
            INTERNAL_URLS=['/tested-url/'],
        ):
            results = get_results_for('test_all_urls_accounted_for')
            self.assertEqual(
                results.failures[0][1][1][0],
                "The following views are untested:\n"
                "^untested-url/$ (name)"
            )
