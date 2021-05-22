import re

from django.conf.urls import url
from django.http import HttpResponse
from django.test import SimpleTestCase

from instant_coverage import optional

from .utils import get_results_for, mocked_patterns


class ValidJSONTest(SimpleTestCase):
    def test_valid_json(self):
        def valid_json(*args, **kwargs):
            return HttpResponse('{}', content_type='application/json')

        def invalid_json(*args, **kwargs):
            return HttpResponse('garbage', content_type='application/json')

        def not_json(*args, **kwargs):
            return HttpResponse('garbage', content_type='text/html')

        with mocked_patterns([
            url(r'^valid/$', valid_json),
            url(r'^invalid/$', invalid_json),
            url(r'^not/$', not_json),
        ]):
            results = get_results_for(
                'test_valid_json', mixin=optional.ValidJSON,
                covered_urls=['/valid/', '/invalid/', '/not/']
            )

            self.assertTrue(
                results.failures[0][1][1].args[0].startswith(
                    "The following URLs returned invalid JSON:\n\n"
                    "/invalid/: ",
                ),
                '"{error}"\n'
                'does not look like the kind of error we expect'.format(
                    error=results.failures[0][1][1].args[0]
                )
            )

    def test_no_json(self):
        """
        Ensure that, given a website with no json in it, a failure is raised.
        """

        def valid_not_json(*args, **kwargs):
            return HttpResponse('{}', content_type='text/plain')

        with mocked_patterns([
            url(r'^valid-not-json/$', valid_not_json),
        ]):
            results = get_results_for(
                'test_valid_json', mixin=optional.ValidJSON,
                covered_urls=['/valid/', '/invalid/', '/not/']
            )

            self.assertEqual(
                results.failures[0][1][1].args[0],
                "No views were found to serve up JSON. Ensure any views you "
                "expect to return JSON set the Content-Type: header to "
                "'application/json'."
            )


class ExternalLinksTest(SimpleTestCase):
    def test_external_links(self):
        def page_with_links(*args, **kwargs):
            return HttpResponse(
                '<a href="http:garbage"></a>'
                '<a href="https://github.com/colons/not-a-real-repo"></a>'
                '<img src="http://localhost:65530"></img>'
                '<form action="http://what"></a>'
                '<a href="http://google.com/"></a>',
                content_type='text/html; utf-8'
            )

        with mocked_patterns([
            url(r'^page/$', page_with_links),
        ]):
            results = get_results_for(
                'test_external_links', mixin=optional.ExternalLinks,
                covered_urls=['/page/'],
            )

            result_string = results.failures[0][1][1].args[0]

            self.assertIn(
                "The following links are broken:\n\n",
                result_string
            )

            self.assertIn(
                "http:garbage: Invalid URL",
                result_string
            )

            self.assertIn(
                "https://github.com/colons/not-a-real-repo: 404\n"
                "shown on /page/",
                result_string
            )

            connection_error_regex = r'(?m).*^{}[^\r\n]+Connection'

            self.assertRegexpMatches(
                result_string, connection_error_regex.format(
                    re.escape('http://localhost:65530: ')
                )
            )

            self.assertRegexpMatches(
                result_string, connection_error_regex.format(
                    re.escape('http://what: ')
                )
            )

            self.assertNotIn("google", result_string)


class ValidHTML5Test(SimpleTestCase):
    def test_valid_json(self):
        def valid_html(*args, **kwargs):
            return HttpResponse('<!doctype html>\n<html></html>')

        def invalid_html(*args, **kwargs):
            return HttpResponse('<!doctype html>\n<div sty=wu">')

        def not_html(*args, **kwargs):
            return HttpResponse('<div sty=wu">', content_type='text/plain')

        with mocked_patterns([
            url(r'^valid/$', valid_html),
            url(r'^invalid/$', invalid_html),
            url(r'^not/$', not_html),
        ]):
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


class SpellingTest(SimpleTestCase):
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

        with mocked_patterns([
            url(r'^well/$', well_spelt),
            url(r'^poorly/$', poorly_spelt),
            url(r'^not/$', not_html),
        ]):
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
            self.assertIn('\nsuggestions: ', result_string)
            self.assertIn('not, ', result_string)
            self.assertIn('\nseen on: /poorly/', result_string)
            self.assertIn('\n\n"saiodjsoiafh"\n', result_string)

            expected_end = (
                "\n\nIf you disagree with any of these, add them to "
                "EverythingTest.spelling_extra_words.")
            self.assertTrue(result_string.endswith(expected_end),
                            '"{0}" does not end with "{1}"'.format(
                                result_string, expected_end))

    def test_no_language_provided(self):
        self.assertRaisesMessage(
            Exception,
            # I'd ask for AttributeError specifically, but for whatever reason
            # that just causes the AttributeError to be reraised.

            'Set EverythingTest.spelling_language to the language you want to '
            'check against (something like "en_GB" or "fr").',

            lambda: get_results_for(
                'test_spelling', mixin=optional.Spelling,
                covered_urls=['/'])
        )


class WCAGZooTest(SimpleTestCase):
    def test_valid_heading_structure(self):
        def valid_headings(*args, **kwargs):
            return HttpResponse(
                '<!doctype html><body>'
                '<h1>hi</h1><h2>fren</h2><h3>this</h3><h4>is</h4><h2>fine</h2>'
                '</html>'
            )

        def invalid_headings(*args, **kwargs):
            return HttpResponse(
                '<!doctype html><body>'
                '<h1>hi</h1><h3 id="bad">this</h3><h4>isnt</h4><h2>fine</h2>'
                '</html>'
            )

        def not_html(*args, **kwargs):
            return HttpResponse('<div sty=wu">', content_type='text/plain')

        with mocked_patterns([
            url(r'^valid/$', valid_headings),
            url(r'^invalid/$', invalid_headings),
            url(r'^not/$', not_html),
        ]):
            results = get_results_for(
                'test_wcag', mixin=optional.WCAGZoo,
                covered_urls=['/valid/', '/invalid/', '/not/'],
                wcag_css_static_dir='.',
            )
            self.assertIn(
                "Some critters in the WCAG Zoo found problems.\n\n/invalid/:",
                results.failures[0][1][1].args[0],
            )
            self.assertIn('Incorrect header found at /html/body/h3',
                          results.failures[0][1][1].args[0])
            self.assertNotIn("/valid/", results.failures[0][1][1].args[0])
            self.assertNotIn("/not/", results.failures[0][1][1].args[0])
