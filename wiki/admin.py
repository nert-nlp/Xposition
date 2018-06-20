from __future__ import absolute_import, unicode_literals

from django import forms
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from mptt.admin import MPTTModelAdmin

from . import editors, models

# import_export django models
from .plugins.metadata import models as ms
from import_export.admin import ImportExportModelAdmin
from import_export import resources
from import_export import fields
from import_export.widgets import ForeignKeyWidget

# from plugins.metadeta import models

class CorpusSentenceResource(resources.ModelResource):
    corpus = fields.Field(
        column_name='corpus_name',
        attribute='corpus',
        widget=ForeignKeyWidget(ms.Corpus, 'name'))

    language = fields.Field(
        column_name='language_name',
        attribute='language',
        widget=ForeignKeyWidget(ms.Language, 'name'))


    class Meta:
        fields = ('corpus', 'sent_id', 'language', 'orthography', 'is_parallel', 'doc_id',
                  'text', 'tokens', 'word_gloss', 'sent_gloss', 'note', 'mwe_markup')


class PTokenAnnotationResource(resources.ModelResource):
    corpus = fields.Field(
        column_name='corpus_name',
        attribute='corpus',
        widget=ForeignKeyWidget(ms.Corpus, 'name'))

    adposition = fields.Field(
        column_name='adposition_name',
        attribute='adposition',
        widget=ForeignKeyWidget(ms.Adposition, 'name'))

    construal = fields.Field(
        column_name='construal_name',
        attribute='construal',
        widget=ForeignKeyWidget(ms.Construal, 'name'))

    sentence = fields.Field(
        column_name='sent_id',
        attribute='sentence',
        widget=ForeignKeyWidget(ms.CorpusSentence, 'sent_id'))

    # usage = fields.Field(
    #     column_name='construal',
    #     attribute='usage',
    #     widget=ForeignKeyWidget(Usage, 'usage'))

    class Meta:
        fields = ('token_indices', 'adposition', 'construal', 'corpus', 'sentence',
                 'obj_case', 'obj_head', 'gov_head', 'gov_obj_syntax', 'adp_pos', 'gov_pos', 'obj_pos', 'gov_supersense',
                 'obj_supersense', 'is_gold', 'annotator_cluster')
        # fields = ('token_indices', 'adposition', 'construal', 'usage', 'corpus', 'sentence',
        #           'obj_case', 'obj_head', 'gov_head', 'gov_obj_syntax', 'adp_pos', 'gov_pos', 'obj_pos',
        #           'gov_supersense',
        #           'obj_supersense', 'is_gold', 'annotator_cluster')


class CorpusSentenceAdmin(ImportExportModelAdmin):
    resource_class = CorpusSentenceResource

class PTokenAnnotationAdmin(ImportExportModelAdmin):
    resource_class = PTokenAnnotationResource



# Django 1.9 deprecation of contenttypes.generic
try:
    from django.contrib.contenttypes.admin import GenericTabularInline
except ImportError:
    from django.contrib.contenttypes.generic import GenericTabularInline


class ArticleObjectAdmin(GenericTabularInline):
    model = models.ArticleForObject
    extra = 1
    max_num = 1
    raw_id_fields = ('article',)


class ArticleRevisionForm(forms.ModelForm):

    class Meta:
        model = models.ArticleRevision
        exclude = ()

    def __init__(self, *args, **kwargs):
        super(ArticleRevisionForm, self).__init__(*args, **kwargs)
        # TODO: This pattern is too weird
        editor = editors.getEditor()
        self.fields['content'].widget = editor.get_admin_widget()


class ArticleRevisionAdmin(admin.ModelAdmin):
    form = ArticleRevisionForm
    list_display = ('title', 'created', 'modified', 'user', 'ip_address')

    class Media:
        js = editors.getEditorClass().AdminMedia.js
        css = editors.getEditorClass().AdminMedia.css


class ArticleRevisionInline(admin.TabularInline):
    model = models.ArticleRevision
    form = ArticleRevisionForm
    fk_name = 'article'
    extra = 1
    fields = ('content', 'title', 'deleted', 'locked',)

    class Media:
        js = editors.getEditorClass().AdminMedia.js
        css = editors.getEditorClass().AdminMedia.css


class ArticleForm(forms.ModelForm):

    class Meta:
        model = models.Article
        exclude = ()

    def __init__(self, *args, **kwargs):
        super(ArticleForm, self).__init__(*args, **kwargs)
        if self.instance.pk:
            revisions = models.ArticleRevision.objects.filter(
                article=self.instance)
            self.fields['current_revision'].queryset = revisions
        else:
            self.fields[
                'current_revision'].queryset = models.ArticleRevision.objects.none()
            self.fields['current_revision'].widget = forms.HiddenInput()


class ArticleAdmin(admin.ModelAdmin):
    inlines = [ArticleRevisionInline]
    form = ArticleForm
    search_fields = ('current_revision__title', 'current_revision__content')


class URLPathAdmin(MPTTModelAdmin):
    inlines = [ArticleObjectAdmin]
    list_filter = ('site', 'articles__article__current_revision__deleted',
                   'articles__article__created',
                   'articles__article__modified')
    list_display = ('__str__', 'article', 'get_created')
    raw_id_fields = ('article',)

    def get_created(self, instance):
        return instance.article.created
    get_created.short_description = _('created')

    def save_model(self, request, obj, form, change):
        """
        Ensure that there is a generic relation from the article to the URLPath
        """
        obj.save()
        obj.article.add_object_relation(obj)


admin.site.register(models.URLPath, URLPathAdmin)
admin.site.register(models.Article, ArticleAdmin)
admin.site.register(models.ArticleRevision, ArticleRevisionAdmin)