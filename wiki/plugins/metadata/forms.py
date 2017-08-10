
from __future__ import absolute_import, unicode_literals
from wiki.models import URLPath
from django.utils.safestring import mark_safe
from django import forms
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext
from wiki.core.plugins.base import PluginSidebarFormMixin
from . import models
from .models import deepest_instance
from wiki.models import Category
from wiki.models import ArticleRevision
import copy, sys


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
            revision.set_from_request(self.request)
            revision.article = supersense.article
            revision.template = "supersense_article_view.html"
            revision.articleRevision = supersense.article.current_revision
            supersense.add_revision(self.instance, save=True)
            if self.cleaned_data['counterpart']:
                counterpart = self.cleaned_data['counterpart'].current_revision.metadatarevision.supersenserevision
                counterpart.counterpart = supersense
                counterpart.save()
            supersense_category = Category(slug=self.data['name'],
                                                          name=self.data['name'],
                                                          description=self.data['description'])
            supersense_category.save()
            supersense.article.categories.add(supersense_category)
            supersense.article.save()
            return self.article_urlpath
        return super(SupersenseForm, self).save(*args, **kwargs)

    class Meta:
        model = models.SupersenseRevision
        fields = ('name', 'description', 'animacy', 'counterpart')

class MetaSidebarForm(forms.Form):

    ''' Multipurpose form that is used in the 'edit sidebar' to dynamically edit different metadata types'''

    def __init__(self, article, request, *args, **kwargs):
        self.article = article
        self.request = request
        super(MetaSidebarForm, self).__init__(*args, **kwargs)

        # Must use try except blocks in order to avoid django errors if an article has no associated metadata

        try:
            self.metadata = models.Supersense.objects.get(article = self.article)
            self.metacurr = deepest_instance(self.metadata.current_revision)
        except:
            pass

        # If metadata is a supersense then set the form to edit the supersense fields

        try:
            if self.metadata.current_revision.metadatarevision.supersenserevision:
                self.form_type = 'supersense'
                self.fields['animacy'] = forms.DecimalField(max_digits=2,decimal_places=0, initial=self.metacurr.animacy)
                self.fields['counterpart'] = forms.ModelChoiceField(queryset=models.Supersense.objects.exclude(current_revision__exact = self.metacurr),
                                                                    initial=self.metacurr.counterpart, required=False)


        # else if not a supersense then set form to edit a default metadata
        # if you want to add a different metadata type to edit then here is the best place to do so

        except:
            self.form_type = 'metadata'

    def get_usermessage(self):
        return ugettext(
            "Metadata changes saved.")

    def save(self, *args, **kwargs):
        if self.is_valid():
            #  supersense saving logic
            if self.form_type is 'supersense':
                """
                oldCounterpart = self.metadata.current_revision.metadatarevision.supersenserevision.counterpart
                oldAnimacy = self.metadata.current_revision.metadatarevision.supersenserevision.animacy
                if oldCounterpart is not self.cleaned_data['counterpart'] or oldAnimacy != self.cleaned_data['animacy']:

                    self.metadata = self.updateMetadata(oldAnimacy,oldCounterpart)

                    #must create new article revision to track changes to metadata
                    self.updateArticle(self.metadata)
                """
                curr = deepest_instance(self.metadata)
                curr.newRevision(self.request, **self.cleaned_data)

                #must include the following data because django-wiki requires it in sidebar forms
                self.cleaned_data['unsaved_article_title'] = self.metadata.current_revision.metadatarevision.supersenserevision.name
                self.cleaned_data['unsaved_article_content'] = self.metadata.current_revision.metadatarevision.supersenserevision.description
                # add any new metadata type save logic here
                return self.metadata



    def __updateMetadata(self, oldAnimacy, oldCounterpart):
        self.metadata.newRevision(self.request)
        if oldAnimacy != self.cleaned_data['animacy']:
            self.metadata.current_revision.animacy = self.cleaned_data['animacy']
        if oldCounterpart is not self.cleaned_data['counterpart']:
            self.metadata = self.metadata.setCounterpart(self.cleaned_data['counterpart'])

            if oldCounterpart is not None:
                oldCounterpart = oldCounterpart.newRevision(self.request)
                oldCounterpart = oldCounterpart.setCounterpart(newCounterpart=None)

            if self.cleaned_data['counterpart'] is not None:
                if self.cleaned_data[
                    'counterpart'].current_revision.metadatarevision.supersenserevision.counterpart is not None:
                    self.cleaned_data[
                        'counterpart'].current_revision.metadatarevision.supersenserevision.counterpart.newRevision(self.request)
                    self.cleaned_data[
                        'counterpart'].current_revision.metadatarevision.supersenserevision.counterpart.setCounterpart(
                        newCounterpart=None)

                self.cleaned_data['counterpart'] =self.cleaned_data['counterpart'].newRevision(self.request)
                self.cleaned_data['counterpart'] = self.cleaned_data['counterpart'].setCounterpart(newCounterpart=self.metadata)
        self.metadata.current_revision.automatic_log = (
        "Animacy: " + str(self.cleaned_data['animacy']) +
        " Counterpart: " + str(self.cleaned_data['counterpart']))
        self.metadata.current_revision.save()
        return self.metadata

    def updateArticle(self, supersense):
        revision = ArticleRevision()
        revision.inherit_predecessor(self.article)
        revision.title = self.article.current_revision.title
        revision.content = self.article.current_revision.content
        revision.user_message = "Metadata change id: " + str(supersense.current_revision.revision_number)
        revision.deleted = False
        revision.set_from_request(self.request)
        self.article.add_revision(revision)
        supersense.current_revision.articleRevision = revision
        supersense.current_revision.save()

class ExampleForm(forms.Form):

    def __init__(self, article, request, *args, **kwargs):
        self.article = article
        self.request = request
        super(ExampleForm, self).__init__(*args, **kwargs)

    example_Title = forms.CharField()
    example_File = forms.FileField()
