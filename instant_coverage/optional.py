"""
Optional mixins for testing stuff you might want to test.
Include them as mixins in test classes that inherit from InstantCoverageMixin.
"""

import json
import sys


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
