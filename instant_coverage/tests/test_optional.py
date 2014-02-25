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
                results.failures[0][1][1].args[0],
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

            result_string = results.failures[0][1][1].args[0]

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


class ValidHTML5Test(FakeURLPatternsTestCase):
    def test_valid_json(self):
        def valid_html(*args, **kwargs):
            return HttpResponse('<!doctype html>\n<html></html>')

        def invalid_html(*args, **kwargs):
            return HttpResponse('<!doctype html>\n<div sty=wu">')

        def not_html(*args, **kwargs):
            return HttpResponse('<div sty=wu">', content_type='text/plain')

        with override_settings(
            ROOT_URLCONF=patterns(
                '',
                url(r'^valid/$', valid_html),
                url(r'^invalid/$', invalid_html),
                url(r'^not/$', not_html),
            ),
        ):
            results = get_results_for(
                'test_valid_html5', mixin=optional.ValidHTML5,
                covered_urls=['/valid/', '/invalid/', '/not/']
            )
            self.assertEqual(
                results.failures[0][1][1].args[0],
                'html5lib raised the following issues:\n\n'
                '/invalid/:\nLine: 2 Col: 12 Unexpected character in unquoted '
                'attribute\n'
                'Line: 2 Col: 13 Expected closing tag. '
                'Unexpected end of file.'
            )


class SpellingTest(FakeURLPatternsTestCase):
    def test_spelling(self):
        def well_spelt(*args, **kwargs):
            return HttpResponse(
                'I am fuelled by the colour of your aluminium armour. '
                'Every fibre of me is paralysed by your laboured defence.'
            )

        def poorly_spelt(*args, **kwargs):
            return HttpResponse(
                'mi am nott no how wordzz saiodjsoiafh'
            )

        def not_html(*args, **kwargs):
            return HttpResponse('nsaiodjsioajds', content_type='text/plain')

        with override_settings(
            ROOT_URLCONF=patterns(
                '',
                url(r'^well/$', well_spelt),
                url(r'^poorly/$', poorly_spelt),
                url(r'^not/$', not_html),
            ),
        ):
            results = get_results_for(
                'test_spelling', mixin=optional.Spelling,
                covered_urls=['/well/', '/poorly/', '/not/'],
                spelling_language='en_GB',
                spelling_extra_words=['wordzz'],
            )

            result_string = results.failures[0][1][1].args[0]

            self.assertNotIn('wordzz', result_string)
            self.assertNotIn('/not/', result_string)
            self.assertNotIn('/well/', result_string)

            expected_start = (
                'Enchant doesn\'t think any of these are actual words:\n\n')
            self.assertTrue(result_string.startswith(expected_start),
                            '"{0}" does not start with "{1}"'.format(
                                result_string, expected_start))

            self.assertIn('/poorly/', result_string)
            self.assertIn('\n\n"nott"\n', result_string)
            self.assertIn('\nsuggestions: not, ', result_string)
            self.assertIn('\nseen on: /poorly/', result_string)
            self.assertIn('\n\n"saiodjsoiafh"\n', result_string)

            expected_end = (
                "\n\nIf you disagree with any of these, add them to "
                "EverythingTest.spelling_extra_words.")
            self.assertTrue(result_string.endswith(expected_end),
                            '"{0}" does not end with "{1}"'.format(
                                result_string, expected_end))

    def test_no_language_provided(self):
        self.assertRaisesMessage(lambda: get_results_for(
            'test_spelling', mixin=optional.Spelling,
            covered_urls=['/well/', '/poorly/', '/not/']),
            'Set EverythingTest.spelling_language to the language you want to '
            'check against. (something like "en_GB" or "fr").'
        )
