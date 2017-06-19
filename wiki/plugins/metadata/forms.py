
from __future__ import absolute_import, unicode_literals

from django.utils.safestring import mark_safe
from django import forms
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext
from wiki.core.plugins.base import PluginSidebarFormMixin
from . import models

class MetadataForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(MetadataForm, self).__init__(*args, **kwargs)

    def save(self, *args, **kwargs):
        super(MetadataForm, self).save(*args, **kwargs)

    class Meta:
        model = models.Metadata
        exclude = ['article']

class SupersenseForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(SupersenseForm, self).__init__(*args, **kwargs)

    def save(self, *args, **kwargs):
        super(SupersenseForm, self).save(*args, **kwargs)

    class Meta:
        model = models.Supersense
        exclude = ['article']

class MetaSidebarForm(forms.Form):
    def __init__(self, article, request, *args, **kwargs):
        self.article = article
        self.request = request
        super(MetaSidebarForm, self).__init__(*args, **kwargs)
        try:
            self.instance = article.metadata
        except:
            pass
        try:
            if self.instance.supersense:
                self.form_type = 'supersense'
                self.fields['name'] = forms.CharField(label='Name', max_length=100)
                self.fields['description'] = forms.CharField(label='Description', max_length=100)
                self.fields['animacy'] = forms.DecimalField(max_digits=2,decimal_places=0)
                self.fields['counterpart'] = forms.CharField(label='Counterpart', max_length=100)
        except:
            self.form_type = 'metadata'
            self.fields['name'] = forms.CharField(label='Name', max_length=100)
            self.fields['description'] = forms.CharField(label='Description', max_length=100)

    def save(self, *args, **kwargs):
        super(MetaSidebarForm, self).save(*args, **kwargs)

    '''class Meta:
        model = models.Metadata
        exclude = ['article']'''


class SupersenseSidebarForm(forms.ModelForm):
    def __init__(self, article, request, *args, **kwargs):
        self.article = article
        self.request = request
        super(SupersenseSidebarForm, self).__init__(*args, **kwargs)
        try:
            self.instance = article.metadata.supersense
        except:
            pass

    def save(self, *args, **kwargs):
        super(SupersenseSidebarForm, self).save(*args, **kwargs)

    class Meta:
        model = models.Supersense
        exclude = ['article']