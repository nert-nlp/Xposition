from __future__ import absolute_import, unicode_literals

from django.conf.urls import include, url
import wiki.plugins.metadata.views as views

urlpatterns = [
  url(r'^$', views.MetadataView.as_view(), name ='metadata_view'),
  url(r'^createlang$', views.LanguageView.as_view(), name='metadata_create_language'),
  url(r'^editlang$', views.LanguageView.as_view(edit=True), name='metadata_edit_language'),
  url(r'^createsupersense$', views.SupersenseView.as_view(), name='metadata_create_supersense'),
  url(r'^editsupersense$', views.SupersenseView.as_view(edit=True), name='metadata_edit_supersense'),
]
