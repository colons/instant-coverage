import sys
import traceback

import django
from django.conf import settings
from django.test.client import Client

from mock import patch
import six


if django.VERSION >= (2, 0):
    from django.urls import URLPattern, URLResolver, resolve
    from django.urls.resolvers import RoutePattern
    RESOLVE_PATH = 'django.urls.URLPattern.resolve'
else:
    from django.core.urlresolvers import (
        RegexURLPattern as URLPattern,
        RegexURLResolver as URLResolver,
        resolve,
    )
    RESOLVE_PATH = 'django.core.urlresolvers.RegexURLPattern.resolve'
    RoutePattern = None

if django.VERSION >= (2, 0):
    from django.urls import clear_url_caches
elif django.VERSION >= (1, 7):
    from django.core.urlresolvers import clear_url_caches
else:
    from django.core.urlresolvers import _resolver_cache

    def clear_url_caches():
        _resolver_cache.clear()


INSTANT_TRACEBACKS_TUTORIAL = (
    'For full tracebacks, set {name}.instant_tracebacks to True.'
)

IGNORE_TUTORIAL = (
    "Add a URL that matches each of these to {name}.covered_urls "
    "(or {name}.uncovered_urls if you don't want to test them).\n"
    "To explicitly ignore entire includes, add the tuple preceeding each "
    "undesired URL (such as ('^admin/',)) to {name}.uncovered_includes."
)

_instant_cache = {}


def get_urlpatterns():
    return __import__(settings.ROOT_URLCONF, {}, {}, ['']).urlpatterns


def extract_all_patterns_from_urlpatterns(patterns, uncovered_includes,
                                          base=()):
    all_patterns = []

    if base in uncovered_includes:
        return []

    for p in patterns:
        if isinstance(p, URLPattern):
            all_patterns.append((base, p))

        elif isinstance(p, URLResolver):
            all_patterns.extend(extract_all_patterns_from_urlpatterns(
                p.url_patterns, uncovered_includes, base + ((
                    p.pattern.regex.pattern if django.VERSION >= (2, 0)
                    else p.regex.pattern
                ),)))

        elif hasattr(p, '_get_callback'):
            all_patterns.append((base, p))

        elif hasattr(p, 'url_patterns') or hasattr(p, '_get_url_patterns'):
            all_patterns.extend(extract_all_patterns_from_urlpatterns(
                patterns, uncovered_includes, base + ((
                    p.pattern.regex.pattern if django.VERSION >= (2, 0)
                    else p.regex.pattern
                ),)))

        else:
            raise TypeError("%s does not appear to be a urlpattern object" % p)

    return all_patterns


class InstantCoverageAPI(object):
    """
    The API provided by InstantCoverageMixin with none of the tests.
    """

    covered_urls = []  # URLs to test

    uncovered_urls = []  # URLs we're okay with not testing

    uncovered_includes = []  # tuples of includes we're okay with not testing
    # (see README for more details)

    instant_tracebacks = False  # show full tracebacks in test_no_errors

    follow_redirects = True  # whether the test client should follow redirects

    def attempt_to_get_internal_url(self, url):
        return self.client.get(url, **self.get_client_kwargs())

    def get_client_kwargs(self):
        return {
            'follow': self.follow_redirects,
        }

    def _get_responses(self):
        responses = {}
        errors = {}

        for url in self.covered_urls:
            try:
                response = self.attempt_to_get_internal_url(url)
            except Exception:
                errors[url] = sys.exc_info()
            else:
                responses[url] = response

        # We cache responses against the class because test runners tend to
        # use a new instance for each test, and we don't want to draw pages
        # more than once.
        _instant_cache[self.__class__] = {
            'responses': responses, 'errors': errors}

    def _get_from_instant_cache(self, key):
        if self.__class__ not in _instant_cache:
            self._get_responses()

        return _instant_cache[self.__class__][key]

    def setUp(self):
        super(InstantCoverageAPI, self).setUp()
        if not hasattr(self, 'client'):
            # django 1.4 does not do this automatically
            self.client = Client()

    def instant_responses(self):
        """
        Return a dictionary of responses, as returned by the Django test
        client, keyed by URL.
        """

        return self._get_from_instant_cache('responses')

    def instant_errors(self):
        return self._get_from_instant_cache('errors')


class InstantCoverageMixin(InstantCoverageAPI):
    def test_all_urls_accounted_for(self):
        """
        Ensure all URLs that have not been explicitly excluded are present in
        self.covered_urls.
        """

        clear_url_caches()
        seen_patterns = set()

        patterns = get_urlpatterns()

        original_resolve = URLPattern.resolve

        def resolve_and_make_note(self, url, *args, **kwargs):
            match = original_resolve(self, url, *args, **kwargs)

            if match:
                seen_patterns.add(self)

            return match

        with patch(RESOLVE_PATH, resolve_and_make_note):
            for url in list(self.covered_urls) + list(self.uncovered_urls):
                resolve(url.split('?')[0])

        all_patterns = extract_all_patterns_from_urlpatterns(
            patterns, self.uncovered_includes)

        not_accounted_for = [p for p in all_patterns
                             if p[1] not in seen_patterns]

        if not_accounted_for:
            raise self.failureException(
                'The following views are untested:\n\n{0}\n\n{1}'.format(
                    '\n'.join([
                        '{base} {route} ({name})'.format(
                            base=base, name=pattern.name, route=(
                                getattr(pattern.pattern, '_route', None) or
                                getattr(pattern.pattern, '_regex', '-')
                                if django.VERSION >= (2, 0)
                                else pattern._regex
                            ),
                        ) for base, pattern in not_accounted_for
                    ]),
                    IGNORE_TUTORIAL.format(name=self.__class__.__name__),
                )
            )

    def test_no_errors(self):
        """
        Ensure no URLs raise unhandled exceptions that would cause 500s.
        """

        errors = self.instant_errors()

        if errors:
            if self.instant_tracebacks:
                raise self.failureException(
                    'The following errors were raised:\n\n{0}'.format(
                        '\n'.join(['{0}: {1}\n{2}'.format(
                            url, error[0], ''.join(
                                traceback.format_exception(*error)
                            )
                        ) for url, error in six.iteritems(errors)])
                    )
                )
            else:
                raise self.failureException(
                    'The following errors were raised:\n\n{0}\n\n{1}'
                    .format(
                        '\n'.join(['{0}: {1}'.format(url, error[1])
                                   for url, error in six.iteritems(errors)]),
                        INSTANT_TRACEBACKS_TUTORIAL.format(
                            name=self.__class__.__name__),
                    )
                )

    def test_acceptable_status_codes(self):
        """
        Ensure all URLs return responses with status codes between 200 and 399.
        """

        bad_status_codes = {}

        for url, response in six.iteritems(self.instant_responses()):
            if not 200 <= response.status_code < 400:
                bad_status_codes[url] = response.status_code

        if bad_status_codes:
            raise self.failureException(
                'The following bad status codes were seen:\n\n{0}'.format(
                    '\n'.join([
                        '{0}: {1}'.format(url, status)
                        for url, status in six.iteritems(bad_status_codes)
                    ])
                )
            )
