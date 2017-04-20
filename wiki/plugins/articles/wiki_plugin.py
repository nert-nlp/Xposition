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

class ArticlePlugin(BasePlugin):

    slug = 'articleplugin'

    sidebar = {
        'headline': _('ArticlePlugin'),
        'icon_class': 'fa-sitemap',
        'template': 'sidebar.html',
        'form_class': forms.SidebarForm,
        'get_form_kwargs': (lambda a: {})
    }

    # basic views
    article_view_class = article.ArticleView
    article_create_view_class = article.Create
    article_delete_view_class = article.Delete
    article_deleted_view_class = article.Deleted
    article_dir_view_class = article.Dir
    article_edit_view_class = article.Edit
    article_preview_view_class = article.Preview
    article_history_view_class = article.History
    article_settings_view_class = article.Settings
    article_source_view_class = article.Source
    article_plugin_view_class = article.Plugin


    article_tab = (_('ArticlePlugin'), "fa fa-sitemap")
    article_view = views.CategoryView.dispatch

    urlpatterns = { 'article': [
      url(r'^$', views.ArticlePluginView.as_view(), name ='article_plugin'),
    ]}

    def __init__(self):	
        # print "I WAS LOADED!"
        pass

registry.register(CategoryPlugin)
