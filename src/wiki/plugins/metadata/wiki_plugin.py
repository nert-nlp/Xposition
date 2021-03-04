# -*- coding: utf-8 -*-
#from wiki.compat import include, url
from django.urls import include, re_path as url
from django.utils.translation import gettext as _
from wiki.core.plugins import registry
from wiki.core.plugins.base import BasePlugin
from wiki.plugins.metadata import settings
from . import views, forms, models

class MetadataPlugin(BasePlugin):

    ''' This initializes the entire plugin, both the edit 'sidebar' class and the metadata 'tab' '''

    slug = settings.SLUG

    urlpatterns = {
        'article': [url('', include('wiki.plugins.metadata.urls'))]
    }

    sidebar = {
        'headline': _('Metadata'),
        'icon_class': 'fa-asterisk',
        'template': 'metadatasidebar.html',
        'form_class': forms.MetaSidebarForm,
        'get_form_kwargs': (lambda a: {})
    }

    article_tab = (_('Metadata'), "fa fa-asterisk")
    article_view = views.MetadataView().dispatch

    class RenderMedia:
        css = {
            'screen': 'wiki/css/metadata.css'
        }
        js = ['wiki/js/modurlify.js']

    def __init__(self):
        # print "I WAS LOADED!"
        pass

registry.register(MetadataPlugin)
