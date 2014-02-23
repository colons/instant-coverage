"""
Optional mixins for testing stuff you might want to test.
Include them as mixins in test classes that inherit from InstantCoverageMixin.
"""

from collections import defaultdict
import json
import sys

from bs4 import BeautifulSoup
import requests


class ValidJSON(object):
    def test_valid_json(self):
        """
        Ensure all responses with Content-Type: application/json are throwing
        out valid JSON.
        """

        bad_json = {}

        for url, response in self.instant_responses().iteritems():
            if response['Content-Type'] != 'application/json':
                continue

            try:
                json.loads(response.content)
            except ValueError:
                bad_json[url] = sys.exc_info()

        if bad_json:
            raise self.failureException(
                'The following URLs returned invalid JSON:\n\n{0}'.format(
                    '\n'.join([
                        '{0}: {1}'.format(url, err[1])
                        for url, err in bad_json.iteritems()
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

        for internal_url, response in self.instant_responses().iteritems():
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
            except requests.RequestException as e:
                bad_responses[external_url] = e
            else:
                if resp.status_code != 200:
                    bad_responses[external_url] = resp.status_code

        if bad_responses:
            raise self.failureException(
                'The following URLs returned invalid JSON:\n\n{0}'.format(
                    '\n\n'.join(['{0}: {1}\nshown on {2}'.format(
                        url, err, ', '.join(external_urls[url])
                    ) for url, err in bad_responses.iteritems()])
                )
            )
