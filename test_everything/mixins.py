from django.conf import settings
from django.core.urlresolvers import resolve

from django_extensions.management.commands.show_urls import (
    extract_views_from_urlpatterns
)


class EverythingMixin(object):
    def test_all_urls_accounted_for(self):
        urlconf = __import__(settings.ROOT_URLCONF, {}, {}, [''])

        accounted_for = [resolve(url).func for url in settings.INTERNAL_URLS]
        all_views = extract_views_from_urlpatterns(urlconf.urlpatterns)

        not_accounted_for = []

        for func, pattern, name in all_views:
            if func not in accounted_for:
                not_accounted_for.append((pattern, name))

        if not_accounted_for:
            raise self.failureException(
                'The following views are untested:\n{0}'.format(
                    '\n'.join([
                        '{0} ({1})'.format(*p) for p in not_accounted_for
                    ])
                )
            )



    def test_no_errors(self):
        errors = {}

        for url in settings.INTERNAL_URLS:
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

