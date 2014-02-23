from django.conf.urls import patterns, url
from django.http import HttpResponse
from django.test import TestCase
from django.test.utils import override_settings

from instant_coverage import optional

from .utils import get_results_for


class ValidJSONTest(TestCase):
    def test_valid_json(self):
        def valid_json(*args, **kwargs):
            return HttpResponse('{}', content_type='application/json')

        def invalid_json(*args, **kwargs):
            return HttpResponse('garbage', content_type='application/json')

        def not_json(*args, **kwargs):
            return HttpResponse('garbage', content_type='text/html')

        with override_settings(
            ROOT_URLCONF=patterns(
                '',
                url(r'^valid/$', valid_json),
                url(r'^invalid/$', invalid_json),
                url(r'^not/$', not_json),
            ),
        ):
            results = get_results_for(
                'test_valid_json', mixin=optional.ValidJSON,
                covered_urls=['/valid/', '/invalid/', '/not/']
            )
            self.assertEqual(
                results.failures[0][1][1][0],
                "The following URLs returned invalid JSON:\n\n"
                "/invalid/: No JSON object could be decoded"
            )
