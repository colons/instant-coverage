"""
Optional mixins for testing stuff you might want to test.
Include them as mixins in test classes that inherit from InstantCoverageMixin.
"""

import re
from collections import defaultdict
from contextlib import closing
import json
import sys

from bs4 import BeautifulSoup
import html5lib
import requests
import six


class ValidJSON(object):
    def test_valid_json(self):
        """
        Ensure all responses with Content-Type: application/json are throwing
        out valid JSON.
        """

        bad_json = {}
        json_seen = False

        for url, response in six.iteritems(self.instant_responses()):
            if response['Content-Type'] != 'application/json':
                continue

            json_seen = True

            content = response.content.decode('utf-8')

            try:
                json.loads(content)
            except ValueError:
                bad_json[url] = sys.exc_info()

        if bad_json:
            raise self.failureException(
                'The following URLs returned invalid JSON:\n\n{0}'.format(
                    '\n'.join([
                        '{0}: {1}'.format(url, err[1])
                        for url, err in six.iteritems(bad_json)
                    ])
                )
            )

        if not json_seen:
            raise self.failureException(
                "No views were found to serve up JSON. Ensure any views you "
                "expect to return JSON set the Content-Type: header to "
                "'application/json'."
            )


class ExternalLinks(object):
    def test_external_links(self):
        """
        Ensure all external links are pointed at URLs that resolve and respond
        with or eventually redirect to somewhere that responds with a 200
        status code.

        If you want to change your user agent or exclude certain URLs or use a
        proxy or something, override attempt_to_get_external_url in your
        subclass.
        """

        external_urls = defaultdict(list)

        for internal_url, response in six.iteritems(self.instant_responses()):
            if response['Content-Type'].split(';')[0] != 'text/html':
                continue

            soup = BeautifulSoup(response.content, "html5lib")

            for attribute in ['href', 'src', 'action']:
                for prefix in ['http:', 'https:']:
                    for element in soup.select(
                        '[{0}^="{1}"]'.format(attribute, prefix)
                    ):
                        external_urls[element[attribute]].append(internal_url)

        self.ensure_all_urls_resolve(external_urls)

    def ensure_all_urls_resolve(self, urls):
        bad_responses = {}

        for url in urls:
            try:
                resp = self.attempt_to_get_external_url(url)
            except Exception as e:
                bad_responses[url] = e
            else:
                if resp.status_code != 200:
                    bad_responses[url] = resp.status_code

        if bad_responses:
            raise self.failureException(
                'The following links are broken:\n\n{0}'.format(
                    '\n\n'.join(['{0}: {1}\nshown on {2}'.format(
                        url, err, ', '.join(urls[url])
                    ) for url, err in six.iteritems(bad_responses)])
                )
            )

    def attempt_to_get_external_url(self, url):
        with closing(
            requests.get(url, allow_redirects=True, stream=True)
        ) as r:
            return r


class ValidHTML5(object):
    def test_valid_html5(self):
        """
        Ensure html5lib thinks our HTML is okay. Will catch really bad stuff
        like dangling tags and asymmetrical attribute quotes but ignores stuff
        like custom attributes and other petty stuff HTMLTidy and the W3
        validator would complain about.
        """

        parser_complaints = {}

        for url, response in six.iteritems(self.instant_responses()):
            if response['Content-Type'].split(';')[0] != 'text/html':
                continue

            parser = html5lib.HTMLParser()
            parser.parse(response.content)

            if parser.errors:
                parser_complaints[url] = parser.errors

        if parser_complaints:
            raise self.failureException(
                'html5lib raised the following issues:\n\n{0}'.format(
                    '\n\n'.join(['{url}:\n{errs}'.format(
                        url=url, errs='\n'.join(
                            ['Line: {l} Col: {c} {err}'.format(
                                l=l, c=c, err=html5lib.constants.E[e] % v)
                             for ((l, c), e, v) in errors]
                        )
                    ) for url, errors in six.iteritems(parser_complaints)])
                )
            )


class Spelling(object):
    def test_spelling(self):
        """
        Test spelling in the language specified in the `spelling_language`
        attribute of the test class. You can specify additional words you
        consider acceptable spellings in a `spelling_extra_words` attribute.

        This test is pretty stupid and I do not recommend adding it to your
        full-time test suite. It will freak out about almost anything in any
        inline <script>s you have and it doesn't care what a proper noun is. It
        can't hurt to run it occasionally and make sure you've not done
        something silly, though.

        Only tests HTML content; we can't be confident about the intent of
        anything else.

        Requires pyenchant. If you're on Python 3, installing pyenchant from
        pypi may prove to be difficult, so you may have to try `pip install
        git+https://github.com/rfk/pyenchant.git` instead.
        """

        try:
            import enchant
        except ImportError:
            raise ImportError(
                'This test requires the pyenchant library.\n'
                '`pip install pyenchant` should set you up, but you may need '
                'some additional packages in order for that install to run.'
            )

        words = defaultdict(set)  # this is probably gonna get pretty big

        if not hasattr(self, 'spelling_language'):
            raise AttributeError(
                'Set {self}.spelling_language to the language you want to '
                'check against (something like "en_GB" or "fr").'.format(
                    self=self.__class__.__name__,
                )
            )

        for url, response in six.iteritems(self.instant_responses()):
            if response['Content-Type'].split(';')[0] != 'text/html':
                continue

            text = BeautifulSoup(response.content, "html5lib").get_text()

            for word in re.findall(r'\b[^_\d\W]+\b', text, flags=re.UNICODE):
                words[word].add(url)

        dictionary = enchant.Dict(self.spelling_language)
        extra_words = getattr(self, 'spelling_extra_words', set())
        bad_words = {}

        for word, urls in six.iteritems(words):
            if word not in extra_words and not dictionary.check(word):
                bad_words[word] = urls

        if bad_words:
            raise self.failureException(
                "Enchant doesn't think any of these are actual words:\n\n"
                "{problems}\n\n"
                "If you disagree with any of these, add them to "
                "{self}.spelling_extra_words.".format(
                    problems='\n\n'.join([
                        '"{word}"\n'
                        'seen on: {urls}\n'
                        'suggestions: {suggestions}'.format(
                            word=word,
                            urls=', '.join(urls),
                            suggestions=', '.join(dictionary.suggest(word)),
                        ) for word, urls in six.iteritems(bad_words)
                    ]),
                    self=self.__class__.__name__,
                )
            )
