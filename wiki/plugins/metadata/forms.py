
from __future__ import absolute_import, unicode_literals
from wiki.models import URLPath
from django.utils.safestring import mark_safe
from django import forms
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext
from wiki.core.plugins.base import PluginSidebarFormMixin
from . import models
from wiki.models import Category


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
            revision.article = metadata.article
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
            supersense.add_revision(self.instance, save=True)
            if self.cleaned_data['counterpart']:
                counterpart = self.cleaned_data['counterpart']
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
            self.instance = article.metadata
        except:
            pass

        # If metadata is a supersense then set the form to edit the supersense fields

        try:
            if self.instance.supersense:
                self.form_type = 'supersense'
                self.fields['animacy'] = forms.DecimalField(max_digits=2,decimal_places=0, initial=self.instance.supersense.animacy)
                self.fields['counterpart'] = forms.ModelChoiceField(queryset=models.Supersense.objects.all(),
                                                                    initial=self.instance.supersense.counterpart, required=False)

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
                supersense = models.Supersense.objects.get(name = self.article.metadata.name)
                supersense.animacy = self.cleaned_data['animacy']
                if supersense.counterpart is not None and supersense.counterpart is not self.cleaned_data['counterpart']:
                    supersense.counterpart.counterpart = None
                    supersense.counterpart.save()
                supersense.counterpart = self.cleaned_data['counterpart']
                supersense.save()
                if self.cleaned_data['counterpart'] is not None:
                    counterpart = models.Supersense.objects.get(name = self.cleaned_data['counterpart'].name)
                    counterpart.counterpart = supersense
                    counterpart.save()
                #must include the following data because django-wiki requires it in sidebar forms
                self.cleaned_data['unsaved_article_title'] = self.article.metadata.name
                self.cleaned_data['unsaved_article_content'] = self.article.metadata.description
            # add any new metadata type save logic here