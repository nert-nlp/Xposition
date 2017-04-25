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
from . import views, settings, forms, models

class CategoryPlugin(BasePlugin):

    slug = 'categories'

    sidebar = {
        'headline': _('Categories'),
        'icon_class': 'fa-sitemap',
        'template': 'sidebar.html',
        'form_class': forms.SidebarForm,
        'get_form_kwargs': (lambda a: {})
    }


    article_tab = (_('Categories'), "fa fa-sitemap")
    article_view = views.CategoryView.dispatch

    urlpatterns = { 'article': [
      url(r'^$', views.CategoryView.as_view(), name ='categories_list'),
    ]}

    def __init__(self):	
        # print "I WAS LOADED!"
        pass

class CategoryEditPlugin(BasePlugin):
    slug = 'categoryEdit'

    sidebar = {
        'headline': _('Category Edit'),
        'icon_class': 'fa-sitemap',
        'template': 'sidebarEdit.html',
        'form_class': forms.EditCategoryForm,
        'get_form_kwargs': (lambda a: {})
    }


    def __init__(self):
        # print "I WAS LOADED!"
        pass


registry.register(CategoryPlugin)
registry.register(CategoryEditPlugin)