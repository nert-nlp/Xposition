
from __future__ import absolute_import, unicode_literals
from wiki.models import URLPath
from django.utils.safestring import mark_safe
from django import forms
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext
from wiki.core.plugins.base import PluginSidebarFormMixin
from . import models
from .models import deepest_instance
from wiki.plugins.categories.models import ArticleCategory
from wiki.models import ArticleRevision
import wiki.forms
from wiki.conf import settings
import copy, sys

'''
class HorizontalRadioSelect(forms.RadioSelect):
    """Adapted from https://stackoverflow.com/a/39538735"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        css_style = 'style="display: inline-block; margin-right: 10px;"'
        self.renderer.outer_html = '<ul{id_attr} style="display: inline-block">{content}</ul>'
        self.renderer.inner_html = '<li ' + css_style + '>{choice_value}{sub_widgets}</li>'
'''


class ArticleMetadataForm(forms.ModelForm):
    """
    Base class for building a form for a model with an associated article,
    and optionally, an associated ArticleCategory.
    The form allows creation of a new model instance with its associated article/category,
    or for editing an existing model instance. (Attaching a new model instance
    to an existing article/category is not supported.)
    Once created, the associated article/category can be edited elsewhere.
    The model instance cannot be detached from the article/category.

    Subclasses are recommended to supply new() and edit() methods
    that will be called by save() as appropriate.
    """
    def __init__(self, article, request, *args, disable_on_edit=('name','slug'), **kwargs):
        self.article = article #kwargs['article']  # the article in the URL path
        self.request = request #kwargs['request']
        super(ArticleMetadataForm, self).__init__(*args, **kwargs)
        if self.instance.id and disable_on_edit:    # editing an existing instance
            for fldname in disable_on_edit:
                self.fields[fldname].disabled = True

    def newArticle(self):
        self.article_urlpath = URLPath.create_article(
            URLPath.root(),
            slug=self.data['slug'],
            title=self.data['name'],
            content=self.data['name'],
            user_message=" ",
            user=self.request.user,
            article_kwargs={'owner': self.request.user,
                            'group': self.article.group,
                            'group_read': self.article.group_read,
                            'group_write': self.article.group_write,
                            'other_read': self.article.other_read,
                            'other_write': self.article.other_write,
                            })
        newarticle = models.Article.objects.get(urlpath = self.article_urlpath)
        return newarticle

    def newArticle_ArticleCategory(self):
        newarticle = self.newArticle()
        newcategory = ArticleCategory(slug=self.data['name'],
                                      name=self.data['name'],
                                      description=self.data.get('description', self.data['name']),
                                      parent=self.cleaned_data['parent'].category if self.cleaned_data.get('parent') else None)
        newcategory.article = newarticle
        newcategory.save()
        return newarticle, newcategory

    def save(self, commit=True):
        m = super(ArticleMetadataForm, self).save(commit=False)
        if self.instance.id:
            return self.edit(m, commit=commit)
        return self.new(m, commit=commit)

class SupersenseForm(ArticleMetadataForm):

    slug = forms.SlugField(max_length=200)

    def __init__(self, article, request, *args, **kwargs):
        super(SupersenseForm, self).__init__(article, request, *args, **kwargs)

        # use horizontal radio buttons (requires metadata.css)
        self.fields['animacy'].widget.attrs={'class': 'inline'}

        # set up the slug text field, modeled after the create article page
        self.fields['slug'].widget = wiki.forms.TextInputPrepend(
            prepend='/', # + self.urlpath.path,
            attrs={
                # Make patterns force lowercase if we are case insensitive to bless the user with a
                # bit of strictness, anyways
                'pattern': '[a-z0-9_-]+' if not settings.URL_CASE_SENSITIVE else '[a-zA-Z0-9_-]+',
                'title': 'Lowercase letters, numbers, hyphens and underscores' if not settings.URL_CASE_SENSITIVE else 'Letters, numbers, hyphens and underscores',
            }
        )

    def edit(self, m, commit=True):
        thesupersense = self.instance.supersense
        thesupersense.newRevision(self.request, commit=commit, **self.cleaned_data)
        # no change to the present model instance (the previous SupersenseRevision)
        return thesupersense.article.urlpath_set.all()[0]

    def new(self, m, commit=True):
        newarticle, newcategory = self.newArticle_ArticleCategory()
        # associate the article with the SupersenseRevision
        m.article = newarticle

        # create the Supersense, add the article, category, and revision
        supersense = models.Supersense()
        supersense.article = newarticle
        supersense.category = newcategory
        supersense.add_revision(m, self.request, article_revision=newarticle.current_revision, save=True) # cannot delay saving the new supersense revision

        if commit:
            m.save()
            supersense.save()
        return self.article_urlpath

    class Meta:
        model = models.SupersenseRevision
        fields = ('name', 'description', 'parent', 'animacy')
        labels = {'description': _('Short Description')}
        widgets = {'animacy': forms.RadioSelect}

class LanguageForm(ArticleMetadataForm):

    def __init__(self, article, request, *args, **kwargs):
        super(LanguageForm, self).__init__(article, request, *args, **kwargs)

        # use horizontal radio buttons (requires metadata.css)
        for f in self.fields.values():
            if isinstance(f.widget, forms.RadioSelect):
                f.widget.attrs={'class': 'inline'}
                f.widget.choices = f.widget.choices[1:] # remove the empty default

    def edit(self, m, commit=True):
        if commit:
            m.save()
        return m.article.urlpath_set.all()[0]

    def new(self, m, commit=True):
        newarticle, newcategory = self.newArticle_ArticleCategory()
        m.article = newarticle
        m.category = newcategory
        if commit:
            m.save()
        return self.article_urlpath

    class Meta:
        model = models.Language
        exclude = ('article', 'deleted', 'current_revision', 'category')
        widgets = {f: forms.RadioSelect for f in {'pre','post','circum','separate_word','clitic_or_affix'}}


def MetaSidebarForm(article, request, *args, **kwargs):
    """
    Each plugin sets a form_class attribute for use when instantiating a sidebar form.
    Setting form_class=MetaSidebarForm allows for dynamic selection of the class
    depending on the type of metadata attached to the article. The classes need
    to be declared separately in order for ModelForm metaclasses to work.
    """
    try:
        metadata = models.SimpleMetadata.objects.get(article = article)
    except models.SimpleMetadata.DoesNotExist:
        try:
            metadata = models.Metadata.objects.get(article = article)
        except models.Metadata.DoesNotExist:
            return EmptySidebarForm()

    metad = deepest_instance(metadata)
    themodel = type(metad)

    if themodel is models.Supersense:
        metac = deepest_instance(metad.current_revision)
        kwargs['instance'] = metac
        x = SupersenseSidebarForm(article, request, metad, *args, **kwargs)
    elif themodel is models.Language:
        kwargs['instance'] = metad
        x = LanguageSidebarForm(article, request, metad, *args, **kwargs)
    return x

class EmptySidebarForm():
    pass

class BaseMetaSidebarForm(PluginSidebarFormMixin):
    def __init__(self, article, request, metad, *args, **kwargs):
        self.article = article
        self.request = request
        self.metadata = metad #models.Metadata.objects.get(article = self.article)


        super(BaseMetaSidebarForm, self).__init__(*args, **kwargs)


class SupersenseSidebarForm(BaseMetaSidebarForm):
    class Meta:
        model = models.SupersenseRevision
        fields = ('animacy', 'description')
        labels = {'description': _('Short Description')}

    def save(self, *args, **kwargs):
        if self.is_valid():
            self.metacurr.newRevision(self.request, **self.cleaned_data)

class LanguageSidebarForm(BaseMetaSidebarForm):
    class Meta:
        model = models.Language
        exclude = ('article', 'deleted', 'current_revision', 'category')

class ExampleForm(forms.Form):

    def __init__(self, article, request, *args, **kwargs):
        self.article = article
        self.request = request
        super(ExampleForm, self).__init__(*args, **kwargs)

    example_Title = forms.CharField()
    example_File = forms.FileField()
