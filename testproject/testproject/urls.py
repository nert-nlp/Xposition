from __future__ import absolute_import, unicode_literals

from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.http.response import HttpResponse
from django.views.static import serve as static_serve
from django_nyt.urls import get_pattern as get_notify_pattern
from wiki.urls import get_pattern as get_wiki_pattern
from django.conf import settings
from django.conf.urls import include, url

admin.autodiscover()

urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
    url(r'^robots.txt', lambda _: HttpResponse('User-agent: *\nDisallow: /')),
    # url(r'^silk/', include('silk.urls', namespace='silk')),
]



urlpatterns += [
    url(r'^notify/', get_notify_pattern()),
    url(r'', get_wiki_pattern())
]

handler500 = 'testproject.views.server_error'
handler404 = 'testproject.views.page_not_found'


if settings.DEBUG:
    import debug_toolbar
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += [
        url(r'^media/(?P<path>.*)$', static_serve, {'document_root': settings.MEDIA_ROOT}),
    ]
    urlpatterns = [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns