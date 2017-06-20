
from __future__ import absolute_import, unicode_literals

from django.utils.safestring import mark_safe
from django import forms
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext
from wiki.core.plugins.base import PluginSidebarFormMixin
from . import models


class MetadataForm(forms.ModelForm):

    ''' This form is used in the creation of a base metadata object/article '''

    def __init__(self, *args, **kwargs):
        super(MetadataForm, self).__init__(*args, **kwargs)

    def save(self, *args, **kwargs):
        super(MetadataForm, self).save(*args, **kwargs)

    class Meta:
        model = models.Metadata
        exclude = ['article']

class SupersenseForm(forms.ModelForm):

    ''' This form is used in the creation of a combined supersense object/article/category '''

    def __init__(self, *args, **kwargs):
        super(SupersenseForm, self).__init__(*args, **kwargs)

    def save(self, *args, **kwargs):
        super(SupersenseForm, self).save(*args, **kwargs)

    class Meta:
        model = models.Supersense
        exclude = ['article']

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
                self.fields['name'] = forms.CharField(label='Name', max_length=100)
                self.fields['description'] = forms.CharField(label='Description', max_length=100)
                self.fields['animacy'] = forms.DecimalField(max_digits=2,decimal_places=0)
                self.fields['counterpart'] = forms.CharField(label='Counterpart', max_length=100)

        # else if not a supersense then set form to edit a default metadata
        # if you want to add a different metadata type to edit then here is the best place to do so

        except:
            self.form_type = 'metadata'
            self.fields['name'] = forms.CharField(label='Name', max_length=100)
            self.fields['description'] = forms.CharField(label='Description', max_length=100)

    def save(self, *args, **kwargs):
        super(MetaSidebarForm, self).save(*args, **kwargs)
