from __future__ import absolute_import, unicode_literals

from wiki.compat import url
from wiki.urls import WikiURLPatterns
import wiki.plugins.metadata.views as views

class XpositionURLPatterns(WikiURLPatterns):
    def get_root_urls(self):
        # customize certain root URLs to override putting them under _plugin/metadata
        root_url_patterns = [
            url(r'^ex/(?P<exnum>\d+)/$', views.PTokenView.as_view(), name='ptoken_view'), #  /ex/3495/
            url('^(?P<lang>[a-z][a-z](-[a-z]+)?)/(?P<corpus>[^/]*[0-9][^/]*)/(?P<sent_id>[^/]+)/$', views.CorpusSentenceView.as_view(), name='corpus_sentence_view'), #  /en/corpus/streusle4.1/reviews-001325-0003
        ]
        #assert False,root_url_patterns
        return root_url_patterns + super(XpositionURLPatterns, self).get_root_urls()

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
