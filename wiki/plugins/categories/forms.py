
from __future__ import absolute_import, unicode_literals

from django import forms
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext
from wiki.core.plugins.base import PluginSidebarFormMixin
from wiki import models
from wiki.plugins.categories.models import Category

class SidebarForm(PluginSidebarFormMixin):

    def __init__(self, article, request, *args, **kwargs):
        self.article = article
        self.request = request
        super(SidebarForm, self).__init__(*args, **kwargs)
        self.fields['categories'].required = True
        self.fields['categories'].label_from_instance = lambda obj: "%s" % obj.short_title
        self.fields['categories'].initial = article.categories.all


    def get_usermessage(self):
        return ugettext(
            "New category set.")

    def save(self, *args, **kwargs):
        if self.is_valid():
            data = self.cleaned_data
            field = data['categories']
            self.article.categories = field
            self.article.save()
        return super(SidebarForm, self).save(*args, **kwargs)

    class Meta:
        model = models.Article
        fields = ('categories',)
