from __future__ import absolute_import, unicode_literals

import import_export
from bitfield import BitField
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
from import_export import widgets
from import_export.widgets import ForeignKeyWidget, IntegerWidget, Widget
from .plugins.categories.models import ArticleCategory
from .models import URLPath, Article
from django.contrib.auth.models import User
from .plugins.metadata.models import deepest_instance

Admin_request = None

class CorpusForeignKeyWidget(ForeignKeyWidget):
    def get_queryset(self, value, row):
        return self.model.objects.filter(
            name=row["corpus_name"],
            version=row["corpus_version"]
        )


class SentenceForeignKeyWidget(ForeignKeyWidget):
    def get_queryset(self, value, row):
        return self.model.objects.filter(
            corpus__name=row["corpus_name"],
            corpus__version=row["corpus_version"],
            sent_id=row["sent_id"]
        )


class ObjCaseWidget(Widget):
    def clean(self, value, row=None, *args, **kwargs):
        return ms.Case[value]

class ObjCasesWidget(Widget):
    def clean(self, value, row=None, *args, **kwargs):
        x = BitField(flags=ms.Case.choices(), default=False)
        x.flags[ms.Case[value]] = True
        return x

class MorphTypeWidget(Widget):
    def clean(self, value, row=None, *args, **kwargs):
        return ms.Adposition.MorphType[value]

class TransitivityWidget(Widget):
    def clean(self, value, row=None, *args, **kwargs):
        return ms.Adposition.Transitivity[value]


class MyFunctions:
    user = User.objects.get(username='admin')


    def __init__(self, request):
        self.request = request


    def newArticle(self, ex_article=None, name=None, slug=None, parent=None):
        article_urlpath = URLPath.create_article(
            parent=parent or URLPath.root(),
            slug=slug,
            title=name,
            content=name,
            user_message=" ",
            user=self.user,
            article_kwargs={'owner': self.user,
                            'group': ex_article.group,
                            'group_read': ex_article.group_read,
                            'group_write': ex_article.group_write,
                            'other_read': ex_article.other_read,
                            'other_write': ex_article.other_write,
                            })
        newarticle = models.Article.objects.get(urlpath=article_urlpath)
        return newarticle



    def newArticle_ArticleCategory(self, ex_article=None, name=None, parent=None, slug=None):
        newarticle = self.newArticle(ex_article=ex_article,
                                     name=name,
                                     slug=slug or name,
                                     parent=parent)
        newcategory = ArticleCategory(slug=name,
                                      name=name,
                                      description='[created by import]',
                                      parent=models.Article.objects.get(urlpath=parent).category if parent else None)
        newcategory.article = newarticle
        newcategory.save()
        return newarticle, newcategory


class CorpusSentenceResource(resources.ModelResource):
    corpus = fields.Field(
        column_name='corpus',
        attribute='corpus',
        widget=CorpusForeignKeyWidget(ms.Corpus, 'name'))

    language = fields.Field(
        column_name='language',
        attribute='language',
        widget=ForeignKeyWidget(ms.Language, 'name'))

    sent_id = fields.Field(attribute='sent_id', widget=widgets.CharWidget())
    orthography = fields.Field(attribute='orthography', widget=widgets.CharWidget())
    is_parallel = fields.Field(attribute='is_parallel', widget=widgets.BooleanWidget())
    doc_id = fields.Field(attribute='doc_id', widget=widgets.CharWidget())
    text = fields.Field(attribute='text', widget=widgets.CharWidget())
    tokens = fields.Field(attribute='tokens', widget=widgets.CharWidget())
    word_gloss = fields.Field(attribute='word_gloss', widget=widgets.CharWidget())
    sent_gloss = fields.Field(attribute='sent_gloss', widget=widgets.CharWidget())
    note = fields.Field(attribute='note', widget=widgets.CharWidget())
    mwe_markup = fields.Field(attribute='mwe_markup', widget=widgets.CharWidget())

    class Meta:
        model = ms.CorpusSentence
        import_id_fields = ('sent_id',)
        fields = ('corpus', 'sent_id', 'language', 'orthography', 'is_parallel', 'doc_id',
                  'text', 'tokens', 'word_gloss', 'sent_gloss', 'note', 'mwe_markup')


class PTokenAnnotationResource(resources.ModelResource):
    token_indices = fields.Field(attribute='token_indices', widget=widgets.CharWidget())
    obj_head = fields.Field(attribute='obj_head', widget=widgets.CharWidget())
    gov_head = fields.Field(attribute='gov_head', widget=widgets.CharWidget())
    gov_obj_syntax = fields.Field(attribute='gov_obj_syntax', widget=widgets.CharWidget())
    adp_pos = fields.Field(attribute='adp_pos', widget=widgets.CharWidget())
    gov_pos = fields.Field(attribute='gov_pos', widget=widgets.CharWidget())
    obj_pos = fields.Field(attribute='obj_pos', widget=widgets.CharWidget())
    gov_supersense = fields.Field(attribute='gov_supersense', widget=widgets.CharWidget())
    obj_supersense = fields.Field(attribute='obj_supersense', widget=widgets.CharWidget())
    is_gold = fields.Field(attribute='is_gold', widget=widgets.BooleanWidget())
    annotator_cluster = fields.Field(attribute='annotator_cluster', widget=widgets.CharWidget())
    is_transitive = fields.Field(attribute='is_transitive', widget=widgets.BooleanWidget())

    obj_case = fields.Field(
        column_name='obj_case',
        attribute='obj_case',
        widget=ObjCaseWidget())

    adposition = fields.Field(
        column_name='adposition_id',
        attribute='adposition',
        widget=ForeignKeyWidget(ms.Adposition))

    construal = fields.Field(
        column_name='construal_id',
        attribute='construal',
        widget=ForeignKeyWidget(ms.Construal))

    sentence = fields.Field(
        column_name='sent_id',
        attribute='sentence',
        widget=SentenceForeignKeyWidget(ms.CorpusSentence, 'sent_id'))


    usage = fields.Field(
        column_name='usage_id',
        attribute='usage',
        widget=ForeignKeyWidget(ms.Usage))

    class Meta:
        model = ms.PTokenAnnotation
        import_id_fields = ('sentence', 'token_indices')
        fields = ('token_indices', 'adposition', 'construal', 'usage', 'sentence',
                  'obj_case', 'obj_head', 'gov_head', 'gov_obj_syntax', 'adp_pos', 'gov_pos', 'obj_pos',
                  'gov_supersense', 'obj_supersense', 'is_gold', 'annotator_cluster', 'is_transitive')


class ConstrualResource(resources.ModelResource):
    role = fields.Field(
        column_name='role_id',
        attribute='role',
        widget=ForeignKeyWidget(ms.Supersense))
    function = fields.Field(
        column_name='function_id',
        attribute='function',
        widget=ForeignKeyWidget(ms.Supersense))

    def save_instance(self, instance, using_transactions=True, dry_run=False):
        m = instance
        article = Article.objects.get(current_revision__title='Locus--Locus')

        role_name = deepest_instance(m.role.current_revision).name
        function_name = deepest_instance(m.function.current_revision).name
        name = self.get_construal_slug(role_name, function_name)
        # slug will be the same as name
        newarticle, newcategory = MyFunctions(Admin_request).newArticle_ArticleCategory(name=name, slug=name, article=article, parent=None)
        m.article = newarticle
        m.category = newcategory
        m.save()

    def get_construal_slug(cls, role_name, function_name):
        return role_name + '--' + function_name


    class Meta:
        model = ms.Construal
        import_id_fields = ('role', 'function')
        fields = ('role', 'function')


class SupersenseRevisionResource(resources.ModelResource):

    name = fields.Field(attribute='name', column_name='supersense_name', widget=widgets.CharWidget())

    # handle revision creation
    def save_instance(self, instance, using_transactions=True, dry_run=False):
        m = instance
        if ms.Supersense.objects.filter(current_revision__metadatarevision__supersenserevision__name=m.name):
            return

        ex_article = Article.objects.get(current_revision__title='Locus')

        # code taken from wiki/plugins/metadata/forms.py
        newarticle, newcategory = MyFunctions(Admin_request).newArticle_ArticleCategory(name=m.name,ex_article=ex_article)
        # associate the article with the SupersenseRevision
        m.article = newarticle

        # create the Supersense, add the article, category, and revision
        supersense = ms.Supersense()
        supersense.article = newarticle
        supersense.category = newcategory
        if m.parent:
            supersense.category.parent = m.parent.category  # the parent category is stored both on the revision and on the Supersense.category
        else:
            supersense.category.parent = None
        supersense.add_revision(m, Admin_request, article_revision=newarticle.current_revision,
                                save=True)  # cannot delay saving the new supersense revision

        m.save()
        supersense.save()

    class Meta:
        model = ms.SupersenseRevision
        import_id_fields = ('name',)
        fields = ('name',)


class AdpositionRevisionResource(import_export.resources.ModelResource):

    name = fields.Field(column_name='adposition_name', attribute='name', widget=widgets.CharWidget())

    lang = fields.Field(
        column_name='language_name',
        attribute='lang',
        widget=ForeignKeyWidget(ms.Language, 'name'))

    morphtype = fields.Field(attribute='morphtype', widget=MorphTypeWidget())
    transitivity = fields.Field(attribute='transitivity', widget=TransitivityWidget())
    # obj_cases = fields.Field(column_name='obj_case', attribute='obj_cases', widget=ObjCasesWidget())

    # handle revision creation
    def save_instance(self, instance, using_transactions=True, dry_run=False):
        m = instance

        ex_article = Article.objects.get(current_revision__title='for')
        lang_article = ms.Language.objects.get(name=m.lang.name).article

        if ms.Adposition.objects.filter(current_revision__metadatarevision__adpositionrevision__lang__name=m.lang.name,
                                 current_revision__metadatarevision__adpositionrevision__name=m.name):
            return

        # code taken from wiki/plugins/metadata/forms.py
        newarticle, newcategory = MyFunctions(Admin_request).newArticle_ArticleCategory(name=m.name,
                                                                                        ex_article=ex_article,
                                                                                        parent=lang_article.urlpath_set.all()[0],
                                                                                        slug='/' + lang_article.urlpath_set.all()[0].path
                                                                                             + m.name)
        # associate the article with the SupersenseRevision
        m.article = newarticle

        # create the Supersense, add the article, category, and revision
        p = ms.Adposition()
        p.article = newarticle
        p.category = newcategory
        p.add_revision(m, Admin_request, article_revision=newarticle.current_revision,
                       save=True)  # cannot delay saving the new adposition revision


        m.save()
        p.save()

    class Meta:
        model = ms.AdpositionRevision
        import_id_fields = ('name', 'lang',)#('name', 'lang')
        fields = ('name', 'lang', 'morphtype', 'transitivity')


class UsageRevisionResource(import_export.resources.ModelResource):
    adposition = fields.Field(
        column_name='adposition_name',
        attribute='adposition',
        widget=ForeignKeyWidget(ms.Adposition))

    construal = fields.Field(
        column_name='role_name',
        attribute='construal',
        widget=ForeignKeyWidget(ms.Construal))

    obj_case = fields.Field(
        column_name='obj_case',
        attribute='obj_case',
        widget=ObjCaseWidget())

    # handle revision creation
    def save_instance(self, instance, using_transactions=True, dry_run=False):
        m = instance

        article = Article.objects.get(adposition__current_revision__metadatarevision__adpositionrevision__name='in',
                                      construal__role__current_revision__metadatarevision__supersenserevision__name='Locus',
                                      construal__function__current_revision__metadatarevision__supersenserevision__name='Locus')

        user = User.objects.get(username='admin')

        # code taken from wiki/plugins/metadata/forms.py
        if len(m.obj_case.choices) < 2:
            case = None
        else:
            case = ms.Case.shortname(m.obj_case)
        caseSlug = '<' + case + '>' if case else ''
        construalSlug = m.construal.article.urlpath_set.all()[0].slug
        name = UsageRevisionResource.get_usage_name(ms.deepest_instance(m.adposition.current_revision).name,
                                                    str(m.construal),
                                                    case)
        newarticle, newcategory = MyFunctions(Admin_request).newArticle_ArticleCategory(article, parent=article.urlpath_set.all()[0],
                                                             name=name,
                                                             slug=caseSlug + construalSlug)
        # associate the article with the SupersenseRevision
        m.article = newarticle
        m.name = name

        # create the Supersense, add the article, category, and revision
        u = ms.Usage()
        u.article = newarticle
        u.category = newcategory
        u.add_revision(m, Admin_request, article_revision=newarticle.current_revision,
                       save=True)  # cannot delay saving the new adposition revision

        m.save()
        u.save()

        return m

    def get_usage_name(cls, adp_name, construal_name, case=None):
        """Provide 'case' only if it is potentially ambiguous for this adposition"""
        casespec = '<' + case + '>' if case else ''
        return adp_name + casespec + ': ' + construal_name

    class Meta:
        model = ms.UsageRevision
        import_id_fields = ('adposition', 'construal')
        fields = ('adposition', 'construal', 'obj_case')


class CorpusSentenceAdmin(ImportExportModelAdmin):
    resource_class = CorpusSentenceResource


class PTokenAnnotationAdmin(ImportExportModelAdmin):
    resource_class = PTokenAnnotationResource


class AdpositionRevisionAdmin(ImportExportModelAdmin):
    resource_class = AdpositionRevisionResource

    # from https://stackoverflow.com/questions/727928/django-admin-how-to-access-the-request-object-in-admin-py-for-list-display-met
    def get_queryset(self, request):
        global Admin_request
        qs = super(AdpositionRevisionAdmin, self).get_queryset(request)
        Admin_request = request
        return qs


class SupersenseRevisionAdmin(ImportExportModelAdmin):
    resource_class = SupersenseRevisionResource

    # from https://stackoverflow.com/questions/727928/django-admin-how-to-access-the-request-object-in-admin-py-for-list-display-met
    def get_queryset(self, request):
        global Admin_request
        qs = super(SupersenseRevisionAdmin, self).get_queryset(request)
        Admin_request = request
        return qs


class UsageRevisionAdmin(ImportExportModelAdmin):
    resource_class = UsageRevisionResource

    # from https://stackoverflow.com/questions/727928/django-admin-how-to-access-the-request-object-in-admin-py-for-list-display-met
    def get_queryset(self, request):
        global Admin_request
        qs = super(UsageRevisionAdmin, self).get_queryset(request)
        Admin_request = request
        return qs


class ConstrualAdmin(ImportExportModelAdmin):
    resource_class = ConstrualResource


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
admin.site.register(ms.CorpusSentence, CorpusSentenceAdmin)
admin.site.register(ms.PTokenAnnotation, PTokenAnnotationAdmin)
admin.site.register(ms.Construal, ConstrualAdmin)
admin.site.register(ms.UsageRevision, UsageRevisionAdmin)
admin.site.register(ms.AdpositionRevision, AdpositionRevisionAdmin)
admin.site.register(ms.SupersenseRevision, SupersenseRevisionAdmin)
