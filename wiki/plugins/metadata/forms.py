
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
        fields = ('__all__')

class SupersenseForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(SupersenseForm, self).__init__(*args, **kwargs)

    def save(self, *args, **kwargs):
        super(SupersenseForm, self).save(*args, **kwargs)

    class Meta:
        model = models.Supersense
        fields = ('__all__')