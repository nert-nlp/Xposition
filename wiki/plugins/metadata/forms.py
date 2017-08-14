
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

class MetadataForm(forms.ModelForm):

    ''' This form is used in the creation of a base metadata object/article '''

    def __init__(self, article, request, *args, **kwargs):
        self.article = article
        self.request = request
        super(MetadataForm, self).__init__(*args, **kwargs)

    def save(self,  *args, **kwargs):
        if not self.instance.id:
            self.article_urlpath = URLPath.create_article(
                URLPath.root(),
                self.data['name'],
                title=self.data['name'],
                content=self.data['description'],
                user_message=" ",
                user=self.request.user,
                article_kwargs={'owner': self.request.user,
                                'group': self.article.group,
                                'group_read': self.article.group_read,
                                'group_write': self.article.group_write,
                                'other_read': self.article.other_read,
                                'other_write': self.article.other_write,
                                })
            metadata = models.Metadata()
            metadata.article = models.Article.objects.get(urlpath = self.article_urlpath)
            kwargs['commit'] = False
            revision = super(MetadataForm, self).save(*args, **kwargs)
            revision.set_from_request(self.request)
            metadata.add_revision(self.instance, save=True)
            return self.article_urlpath
        return super(MetadataForm, self).save(*args, **kwargs)

    class Meta:
        model = models.MetadataRevision
        fields = ('name', 'description',)

class SupersenseForm(forms.ModelForm):

    ''' This form is used in the creation of a combined supersense object/article/category '''

    def __init__(self, article, request, *args, **kwargs):
        self.article = article
        self.request = request
        super(SupersenseForm, self).__init__(*args, **kwargs)

    def save(self, *args, **kwargs):
        if not self.instance.id:
            self.article_urlpath = URLPath.create_article(
                URLPath.root(),
                self.data['name'],
                title=self.data['name'],
                content=self.data['description'],
                user_message=" ",
                user=self.request.user,
                article_kwargs={'owner': self.request.user,
                                'group': self.article.group,
                                'group_read': self.article.group_read,
                                'group_write': self.article.group_write,
                                'other_read': self.article.other_read,
                                'other_write': self.article.other_write,
                                })
            supersense = models.Supersense()
            supersense.article = models.Article.objects.get(urlpath = self.article_urlpath)
            kwargs['commit'] = False
            revision = super(SupersenseForm, self).save(*args, **kwargs)
            #revision.set_from_request(self.request)

            supersense_category = ArticleCategory(slug=self.data['name'],
                                           name=self.data['name'],
                                           description=self.data['description'],
                                           parent=self.cleaned_data['parent'].category if self.cleaned_data['parent'] else None)
            supersense_category.article = supersense.article
            supersense_category.save()
            supersense.category = supersense_category

            #supersense.article.category = supersense_category


            revision.article = supersense.article
            revision.template = "supersense_article_view.html"
            #supersense.add_revision(self.instance)
            supersense.add_revision(revision, self.request)

            #supersense.article.categories.add(supersense_category) # don't add category landing article to its category
            #supersense.article.category.save()
            supersense.article.save()
            return self.article_urlpath
        return super(SupersenseForm, self).save(*args, **kwargs)

    class Meta:
        model = models.SupersenseRevision
        fields = ('name', 'description', 'parent', 'animacy')
        labels = {'description': _('Short Description')}
        widgets = {'animacy': forms.RadioSelect}


def MetaSidebarForm(article, request, *args, **kwargs):
    """
    Each plugin sets a form_class attribute for use when instantiating a sidebar form.
    Setting form_class=MetaSidebarForm allows for dynamic selection of the class
    depending on the type of metadata attached to the article. The classes need
    to be declared separately in order for ModelForm metaclasses to work.
    """
    try:
        metadata = models.Metadata.objects.get(article = article)
    except models.Metadata.DoesNotExist:
        return EmptySidebarForm()

    metacurr = deepest_instance(metadata)
    themodel = type(metacurr)

    if themodel is models.Supersense:
        kwargs['instance'] = deepest_instance(metacurr.current_revision)
        x = SupersenseSidebarForm(article, request, *args, **kwargs)
    return x

class EmptySidebarForm():
    pass

class BaseMetaSidebarForm(PluginSidebarFormMixin):
    def __init__(self, article, request, *args, **kwargs):
        self.article = article
        self.request = request
        self.metadata = models.Metadata.objects.get(article = self.article)
        self.metacurr = deepest_instance(self.metadata)
        super(BaseMetaSidebarForm, self).__init__(*args, **kwargs)

class SupersenseSidebarForm(BaseMetaSidebarForm):
    def save(self, *args, **kwargs):
        if self.is_valid():
            self.metacurr.newRevision(self.request, **self.cleaned_data)

    class Meta:
        model = models.SupersenseRevision
        fields = ('animacy', 'description')
        labels = {'description': _('Short Description')}

class ExampleForm(forms.Form):

    def __init__(self, article, request, *args, **kwargs):
        self.article = article
        self.request = request
        super(ExampleForm, self).__init__(*args, **kwargs)

    example_Title = forms.CharField()
    example_File = forms.FileField()
