from django.conf import settings
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.http.response import HttpResponse
from django.views.static import serve as static_serve
# from wiki.compat import include, url
from django_nyt.urls import get_pattern as get_notify_pattern
from wiki.urls import get_pattern as get_wiki_pattern
from django.conf import settings
from django.conf.urls import include, url
from django.views.generic.base import RedirectView

admin.autodiscover()

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^robots.txt', lambda _: HttpResponse('User-agent: *\nDisallow: /')),
    # url(r'^silk/', include('silk.urls', namespace='silk')),
    url(r'^favicon\.ico$', RedirectView.as_view(url='/media/wiki/images/favicon.ico')), # need this to tell Chrome where to find the favicon. Note that png doesnt work.
]



urlpatterns += [
    url(r'^notify/', include('django_nyt.urls')),
    url(r'', include('wiki.urls')),
]

handler500 = 'xp.views.server_error'
handler404 = 'xp.views.page_not_found'


if settings.DEBUG:
    import debug_toolbar
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += [
        url(r'^media/(?P<path>.*)$', static_serve, {'document_root': settings.MEDIA_ROOT}),
    ]
    urlpatterns = [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
