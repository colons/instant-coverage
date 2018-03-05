"""
Optional mixins for testing stuff you might want to test.
Include them as mixins in test classes that inherit from InstantCoverageMixin.
"""

import re
from collections import defaultdict
from contextlib import closing
import json
from pprint import pformat
import sys

from django.conf import settings

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
                            ['Line: {line} Col: {col} {err}'.format(
                                line=l, col=c, err=html5lib.constants.E[e] % v)
                             for ((l, c), e, v) in errors]
                        )
                    ) for url, errors in six.iteritems(parser_complaints)])
                )
            )


class WCAGZoo(object):
    wcag_critters = ['parade']
    wcag_level = 'AA'
    wcag_css_static_dir = None

    def test_wcag(self, *args, **kwargs):
        """
        Test HTML for WCAG compliance using critters from WCAG Zoo. If you want
        to only use some of the critters, provide a list of them by name in the
        `wcag_critters` attribute; for instance `['molerat', 'tarsier']`. Have
        a look at the WCAG Zoo documentation for information about what each of
        these critters does. The default, `['parade']`, nests all other
        critters.

        You can also set the `wcag_level` attribute to 'A', 'AA', or 'AAA',
        which affects things like how picky molerat will be about contrast
        levels. Again, see the WCAG Zoo documentation for more detail.

        If you're using Python 2 and have any non-ascii css, you'll probably
        want to use my py2-supporting fork of wcag-zoo, which is available at
        https://github.com/colons/wcag-zoo.
        """

        try:
            from wcag_zoo.utils import get_wcag_class
        except ImportError:
            raise ImportError(
                'This test requires wcag-zoo.\n'
                '`pip install wcag-zoo` will work if you are running a '
                'version of Python 3, but for 2.7 you will need a version '
                'with 2.7 support, like https://github.com/colons/wcag-zoo'
            )

        results = {}
        staticpath = self.wcag_css_static_dir
        if staticpath is None:
            try:
                staticpath, = settings.STATICFILES_DIRS
            except ValueError:
                raise RuntimeError(
                    'Could not determine a single static directory to look '
                    'for your CSS in. Please ensure that your Django '
                    'STATICFILES_DIRS setting is a single directory, or set '
                    '{}.wcag_css_static_dir to the path you want us to look '
                    'in instead.'
                    .format(self.__class__.__name__)
                )

        for critter_name in self.wcag_critters:
            for url, response in six.iteritems(self.instant_responses()):
                if response['Content-Type'].split(';')[0] != 'text/html':
                    continue

                soup = BeautifulSoup(response.content, 'html5lib')
                for style in soup.select('link[rel="stylesheet"]'):
                    if style['href'].startswith(settings.STATIC_URL):
                        style['href'] = style['href'].replace(
                            settings.STATIC_URL, '', 1,
                        )

                critter = get_wcag_class(critter_name)(
                    level=self.wcag_level, staticpath=staticpath,
                )

                result = critter.validate_document(
                    six.text_type(soup).encode('utf-8')
                )

                if result['failures']:
                    error_list = results.setdefault(url, [])
                    error_list.append(result['failures'])

        if results:
            raise self.failureException(
                u'Some critters in the WCAG Zoo found problems.\n\n{}'.format(
                    u'\n\n'.join((
                        u'{}:\n{}'.format(
                            url,
                            u'\n'.join(
                                pformat(e) for e in errors
                            ),
                        ) for url, errors in six.iteritems(results)
                    ))
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

        Requires pyenchant.
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
