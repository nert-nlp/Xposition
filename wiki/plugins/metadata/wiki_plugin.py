# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.forms import modelform_factory
from django.conf.urls import include, url
from django.utils.translation import ugettext as _
from wiki.core.plugins import registry
from wiki.models import Article
from wiki.core.plugins.base import BasePlugin
from wiki.plugins.notifications.settings import ARTICLE_EDIT
from wiki.plugins.notifications.util import truncate_title
from . import views, forms, models

class MetadataPlugin(BasePlugin):

    slug = 'metadata'

    sidebar = {
        'headline': _('Metadata'),
        'icon_class': 'fa-asterisk',
        'template': 'metadatasidebar.html',
        'form_class': forms.MetaSidebarForm,
        'get_form_kwargs': (lambda a: {})
    }

    article_tab = (_('Metadata'), "fa fa-asterisk")
    article_view = views.MetadataView.dispatch

    urlpatterns = { 'article': [
      url(r'^$', views.MetadataView.as_view(), name ='metadata_view'),
    ]}

    def __init__(self):
        # print "I WAS LOADED!"
        pass


'''class SupersensePlugin(BasePlugin):

    slug = 'supersense'

    sidebar = {
        'headline': _('Supersense'),
        'icon_class': 'fa-asterisk',
        'template': 'metadatasidebar.html',
        'form_class': forms.SupersenseSidebarForm,
        'get_form_kwargs': (lambda a: {})
    }

    def __init__(self):
        # print "I WAS LOADED!"
        pass

registry.register(SupersensePlugin)'''
registry.register(MetadataPlugin)