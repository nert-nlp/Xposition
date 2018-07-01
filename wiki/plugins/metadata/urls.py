from __future__ import absolute_import, unicode_literals

from django.conf.urls import include, url
import wiki.plugins.metadata.views as views

urlpatterns = [
  url(r'^$', views.MetadataView.as_view(), name ='metadata_view'),
  url(r'^installmetadata/$', views.InstallView.as_view(), name='metadata_install_view'),
  url(r'^createlang/$', views.LanguageView.as_view(), name='metadata_create_language'),
  url(r'^editlang/$', views.LanguageView.as_view(edit=True), name='metadata_edit_language'),
  url(r'^createp/$', views.AdpositionView.as_view(), name='metadata_create_adposition'),
  url(r'^editp/$', views.AdpositionView.as_view(edit=True), name='metadata_edit_adposition'),
  url(r'^createusage/$', views.UsageView.as_view(), name='metadata_create_usage'),
  url(r'^editusage/$', views.UsageView.as_view(edit=True), name='metadata_edit_usage'),
  url(r'^createconstrual/$', views.ConstrualView.as_view(), name='metadata_create_construal'),
  url(r'^createsupersense/$', views.SupersenseView.as_view(), name='metadata_create_supersense'),
  url(r'^editsupersense/$', views.SupersenseView.as_view(edit=True), name='metadata_edit_supersense'),
  url(r'^createcorpus/$', views.CorpusView.as_view(), name='metadata_create_corpus'),
  url(r'^editcorpus/$', views.CorpusView.as_view(edit=True), name='metadata_edit_corpus'),
]
