from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class MetadataConfig(AppConfig):
    name = 'wiki.plugins.metadata'
    verbose_name = _("Wiki metadata")
    label = 'metadata'
