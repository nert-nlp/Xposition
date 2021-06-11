from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class HelpConfig(AppConfig):
    name = "wiki.plugins.help"
    verbose_name = _("Wiki help")
    label = "wiki_help"
