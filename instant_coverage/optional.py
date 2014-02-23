"""
Optional mixins for testing stuff you might want to test.
Include them as mixins in test classes that inherit from InstantCoverageMixin.
"""

from collections import defaultdict
import json
import sys

from bs4 import BeautifulSoup
import requests
import html5lib
import six


class ValidJSON(object):
    def test_valid_json(self):
        """
        Ensure all responses with Content-Type: application/json are throwing
        out valid JSON.
        """

        bad_json = {}

        for url, response in six.iteritems(self.instant_responses()):
            if response['Content-Type'] != 'application/json':
                continue

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


class ExternalLinks(object):
    def test_external_links(self):
        """
        Ensure all external links are pointed at URLs that resolve and respond
        with or eventually redirect to somewhere that responds with a 200
        status code.
        """

        external_urls = defaultdict(list)

        for internal_url, response in six.iteritems(self.instant_responses()):
            if response['Content-Type'].split(';')[0] != 'text/html':
                continue

            soup = BeautifulSoup(response.content)

            for attribute in ['href', 'src']:
                for prefix in ['http:', 'https:']:
                    for element in soup.select(
                        '[{0}^="{1}"]'.format(attribute, prefix)
                    ):
                        external_urls[element[attribute]].append(internal_url)

        bad_responses = {}

        for external_url in external_urls:
            try:
                resp = requests.get(external_url)
            except Exception as e:
                bad_responses[external_url] = e
            else:
                if resp.status_code != 200:
                    bad_responses[external_url] = resp.status_code

        if bad_responses:
            raise self.failureException(
                'The following external links are broken:\n\n{0}'.format(
                    '\n\n'.join(['{0}: {1}\nshown on {2}'.format(
                        url, err, ', '.join(external_urls[url])
                    ) for url, err in six.iteritems(bad_responses)])
                )
            )


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
                    ) for url, errors in six.iteritems(parser_complaints)])))
