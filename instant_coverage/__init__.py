from django.conf.urls import url
from django.conf import settings
from django.core.urlresolvers import (
    RegexURLPattern, RegexURLResolver, resolve, _resolver_cache
)
from django.test import TestCase as BaseCase

from mock import patch


SEEN_PATTERNS = set()
# we could do this with a closure, but for the moment i just want to see it
# work


class URLSurfacingRegexURLPattern(RegexURLPattern):
    """
    A subclass of RegexURLPattern that runs a callback with a URL when
    successfully matching with it
    """

    def __init__(self, *args, **kwargs):
        super(URLSurfacingRegexURLPattern, self).__init__(*args, **kwargs)

    def resolve(self, url, *args, **kwargs):
        match = super(URLSurfacingRegexURLPattern, self
                      ).resolve(url, *args, **kwargs)
        if match:
            SEEN_PATTERNS.add(self)

        return match


def url_with_url_sufacing_url_patterns(*args, **kwargs):
    with patch('django.conf.urls.RegexURLPattern',
               URLSurfacingRegexURLPattern):
        return url(*args, **kwargs)


def get_urlpatterns():
    with patch('django.conf.urls.url',
               url_with_url_sufacing_url_patterns):
        return __import__(settings.ROOT_URLCONF, {}, {}, ['']).urlpatterns


def extract_all_patterns_from_urlpatterns(patterns, base=()):
    all_patterns = []

    if base in getattr(settings, 'UNCOVERED_INCLUDES', []):
        return []

    for p in patterns:
        if isinstance(p, RegexURLPattern):
            all_patterns.append((base, p))
        elif isinstance(p, RegexURLResolver):
            all_patterns.extend(extract_all_patterns_from_urlpatterns(
                p.url_patterns, base + (p.regex.pattern,)))
        elif hasattr(p, '_get_callback'):
            all_patterns.append((base, p))
        elif hasattr(p, 'url_patterns') or hasattr(p, '_get_url_patterns'):
            all_patterns.extend(extract_all_patterns_from_urlpatterns(
                patterns, base + (p.regex.pattern,)))
        else:
            raise TypeError("%s does not appear to be a urlpattern object" % p)

    return all_patterns


class TestCase(BaseCase):
    def test_all_urls_accounted_for(self):
        """
        Ensure all URLs that have not been explicitly excluded are present in
        settings.INTERNAL_URLS.
        """

        _resolver_cache.clear()
        SEEN_PATTERNS.clear()

        patterns = get_urlpatterns()

        for url in (
            settings.COVERED_URLS + getattr(settings, 'UNCOVERED_URLS', [])
        ):
            resolve(url)

        all_patterns = extract_all_patterns_from_urlpatterns(patterns)
        not_accounted_for = [p for p in all_patterns
                             if p[1] not in SEEN_PATTERNS]

        if not_accounted_for:
            raise self.failureException(
                'The following views are untested:\n{0}'.format(
                    '\n'.join([
                        '{base} {_regex} ({name})'.format(
                            base=base, **pattern.__dict__
                        ) for base, pattern in not_accounted_for
                    ])
                )
            )

    def test_no_errors(self):
        """
        Ensure no URLs raise unhandled exceptions that would cause 500s.
        """

        errors = {}

        for url in settings.COVERED_URLS:
            try:
                self.client.get(url)
            except Exception as e:
                errors[url] = e

        if errors:
            raise self.failureException(
                'The following errors were raised:\n{0}'.format(
                    '\n'.join([
                        '{0}: {1}'.format(*e) for e in errors.iteritems()
                    ])
                )
            )
