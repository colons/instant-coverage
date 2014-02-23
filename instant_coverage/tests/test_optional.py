from django.conf.urls import patterns, url
from django.http import HttpResponse
from django.test.utils import override_settings

from instant_coverage import optional

from .utils import get_results_for, FakeURLPatternsTestCase


class ValidJSONTest(FakeURLPatternsTestCase):
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


class ExternalLinksTest(FakeURLPatternsTestCase):
    def test_external_links(self):
        def page_with_links(*args, **kwargs):
            return HttpResponse(
                '<a href="http:garbage"></a>'
                '<a href="https://github.com/colons/not-a-real-repo"></a>'
                '<img src="http://localhost:9000000"></img>'
                '<a href="http://what"></a>'
                '<a href="http://google.com/"></a>',
                content_type='text/html; utf-8'
            )

        with override_settings(
            ROOT_URLCONF=patterns(
                '',
                url(r'^page/$', page_with_links),
            ),
        ):
            results = get_results_for(
                'test_external_links', mixin=optional.ExternalLinks,
                covered_urls=['/page/'],
            )

            result_string = results.failures[0][1][1][0]

            self.assertIn(
                "The following external links are broken:\n\n",
                result_string
            )

            self.assertIn(
                "http:garbage: Failed to parse: Failed to parse: http:garbage"
                "\nshown on /page/",
                result_string
            )

            self.assertIn(
                "https://github.com/colons/not-a-real-repo: 404\n"
                "shown on /page/",
                result_string
            )

            self.assertIn(
                "http://localhost:9000000: HTTPConnectionPool(", result_string
            )

            self.assertIn(
                "http://what: HTTPConnectionPool(", result_string
            )

            self.assertNotIn("google", result_string)
