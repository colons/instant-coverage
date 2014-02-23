import sys
import traceback

from django.conf import settings
from django.core.urlresolvers import (
    RegexURLPattern, RegexURLResolver, resolve, _resolver_cache
)

from mock import patch


INSTANT_TRACEBACKS_TUTORIAL = (
    'For full tracebacks, set {name}.instant_tracebacks to True.'
)

IGNORE_TUTORIAL = (
    "Add a URL that matches each of these to {name}.covered_urls "
    "(or {name}.uncovered_urls if you don't want to test them).\n"
    "To explicitly ignore entire includes, add the tuple preceeding each "
    "undesired URL (such as ('^admin/',)) to {name}.uncovered_includes."
)


def get_urlpatterns():
    return __import__(settings.ROOT_URLCONF, {}, {}, ['']).urlpatterns


def extract_all_patterns_from_urlpatterns(patterns, uncovered_includes,
                                          base=()):
    all_patterns = []

    if base in uncovered_includes:
        return []

    for p in patterns:
        if isinstance(p, RegexURLPattern):
            all_patterns.append((base, p))

        elif isinstance(p, RegexURLResolver):
            all_patterns.extend(extract_all_patterns_from_urlpatterns(
                p.url_patterns, uncovered_includes, base + (p.regex.pattern,)))

        elif hasattr(p, '_get_callback'):
            all_patterns.append((base, p))

        elif hasattr(p, 'url_patterns') or hasattr(p, '_get_url_patterns'):
            all_patterns.extend(extract_all_patterns_from_urlpatterns(
                patterns, uncovered_includes, base + (p.regex.pattern,)))

        else:
            raise TypeError("%s does not appear to be a urlpattern object" % p)

    return all_patterns


class InstantCoverageMixin(object):
    covered_urls = []
    uncovered_urls = []
    uncovered_includes = []
    instant_tracebacks = False

    def _get_responses(self):
        # We cache responses against the class because test runners tend to
        # use a new instance for each test, and we don't want to draw pages
        # more than once.

        responses = {}
        errors = {}

        for url in self.covered_urls:
            try:
                response = self.client.get(url)
            except Exception:
                errors[url] = sys.exc_info()
            else:
                responses[url] = response

        self.__class__._instant_cache = (responses, errors)

    def responses(self):
        if not hasattr(self.__class__, '_instant_cache'):
            self._get_responses()

        return self.__class__._instant_cache

    def test_all_urls_accounted_for(self):
        """
        Ensure all URLs that have not been explicitly excluded are present in
        self.covered_urls.
        """

        _resolver_cache.clear()
        seen_patterns = set()

        patterns = get_urlpatterns()

        original_resolve = RegexURLPattern.resolve

        def resolve_and_make_note(self, url, *args, **kwargs):
            match = original_resolve(self, url, *args, **kwargs)

            if match:
                seen_patterns.add(self)

            return match

        with patch('django.core.urlresolvers.RegexURLPattern.resolve',
                   resolve_and_make_note):
            for url in self.covered_urls + self.uncovered_urls:
                resolve(url)

        all_patterns = extract_all_patterns_from_urlpatterns(
            patterns, self.uncovered_includes)

        not_accounted_for = [p for p in all_patterns
                             if p[1] not in seen_patterns]

        if not_accounted_for:
            raise self.failureException(
                'The following views are untested:\n\n{0}\n\n{1}'.format(
                    '\n'.join([
                        '{base} {_regex} ({name})'.format(
                            base=base, **pattern.__dict__
                        ) for base, pattern in not_accounted_for
                    ]),
                    IGNORE_TUTORIAL.format(name=self.__class__.__name__),
                )
            )

    def test_no_errors(self):
        """
        Ensure no URLs raise unhandled exceptions that would cause 500s.
        """

        responses, errors = self.responses()

        if errors:
            if self.instant_tracebacks:
                raise self.failureException(
                    'The following errors were raised:\n\n{0}'.format(
                        '\n'.join(['{0}: {1}\n{2}'.format(
                            url, error[0], ''.join(
                                traceback.format_exception(*error)
                            )
                        ) for url, error in errors.iteritems()])
                    )
                )
            else:
                raise self.failureException(
                    'The following errors were raised:\n\n{0}\n\n{1}'
                    .format(
                        '\n'.join(['{0}: {1}'.format(url, error[1])
                                   for url, error in errors.iteritems()]),
                        INSTANT_TRACEBACKS_TUTORIAL.format(
                            name=self.__class__.__name__),
                    )
                )

    def test_acceptable_response_codes(self):
        """
        Ensure all URLs return responses with status codes between 200 and 399.
        """

        responses, errors = self.responses()
        bad_status_codes = {}

        for url, response in responses.iteritems():
            if not 200 <= response.status_code < 400:
                bad_status_codes[url] = response.status_code

        if bad_status_codes:
            raise self.failureException(
                'The following bad status codes were seen:\n\n{0}'.format(
                    '\n'.join([
                        '{0}: {1}'.format(url, status)
                        for url, status in bad_status_codes.iteritems()
                    ])
                )
            )
