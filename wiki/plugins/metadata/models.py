from django.core.urlresolvers import reverse
from django.db import models
from django.utils.encoding import force_text
from django.contrib.contenttypes.models import ContentType
from functools import reduce
from wiki.models import Article
from django.contrib import admin
try:
    from django.contrib.contenttypes.fields import GenericForeignKey
except ImportError:
    from django.contrib.contenttypes.generic import GenericForeignKey
from django.core.files.storage import get_storage_class

from django.utils.translation import ugettext_lazy as _


class Metadata(models.Model):
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=200)
    article = models.OneToOneField(Article, null=True)

    class Meta():
        verbose_name = _('metadata')


class Supersense(Metadata):
    animacy = models.DecimalField(max_digits=100, decimal_places=0)
    counterpart = models.CharField(max_length=100)


admin.site.register(Metadata)
admin.site.register(Supersense)