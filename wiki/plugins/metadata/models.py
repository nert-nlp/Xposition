from django.core.urlresolvers import reverse
from django.db import models
from django.utils.encoding import force_text
from django.contrib.contenttypes.models import ContentType
from functools import reduce
from wiki.models import Article
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext
from django.contrib import admin
from wiki.models.pluginbase import RevisionPlugin, RevisionPluginRevision
try:
    from django.contrib.contenttypes.fields import GenericForeignKey
except ImportError:
    from django.contrib.contenttypes.generic import GenericForeignKey
from django.core.files.storage import get_storage_class

from django.utils.translation import ugettext_lazy as _

# These are the different metadata models. Extend from the base metadata class if you want to add a
# new metadata type. Make sure to register your model below.

class Metadata(RevisionPlugin):

    def __str__(self):
        if self.current_revision:
            return self.current_revision.metadatarevision.name
        else:
            return ugettext('Current revision not set!!')

    class Meta():
        verbose_name = _('metadata')

class MetadataRevision(RevisionPluginRevision):
    article = models.OneToOneField(Article, null=True)
    template = models.CharField(max_length=100, default="wiki/view.html", editable=False)
    name = models.CharField(max_length=100, primary_key=True)
    description = models.CharField(max_length=200)

    def __str__(self):
        return ('Supersense Revision: %s %d') % (self.name, self.revision_number)

    class Meta:
        verbose_name = _('metadata revision')


class Supersense(Metadata):

    def newRevision(self):
        article = self.current_revision.metadatarevision.supersenserevision.article
        oldRevision = self.current_revision.metadatarevision.supersenserevision
        revision = SupersenseRevision(name=oldRevision.name,
                                             description=oldRevision.description,
                                             animacy=oldRevision.animacy,
                                             counterpart=oldRevision.counterpart,
                                             template="supersense_article_view.html",
                                             article=oldRevision.article)
        article.metadatarevision = revision
        article.save()
        oldRevision.article = None
        oldRevision.save()
        self.add_revision(revision, save=True)
        revision.save()
        return revision


    def setCounterpart(self, newCounterpart):
        revision = self.current_revision.metadatarevision.supersenserevision
        oldCounterpart = self.current_revision.metadatarevision.supersenserevision.counterpart

        if newCounterpart is not oldCounterpart:
            revision.counterpart = newCounterpart
            revision.save()


    def __str__(self):
        if self.current_revision:
            return self.current_revision.metadatarevision.name
        else:
            return ugettext('Current revision not set!!')
    class Meta:
        verbose_name = _('supersense')

class SupersenseRevision(MetadataRevision):
    animacy = models.DecimalField(max_digits=2, decimal_places=0)
    counterpart = models.ForeignKey(Supersense, null=True, blank=True)

    def __str__(self):
        return ('Supersense Revision: %s %d') % (self.name, self.revision_number)

    class Meta:
        verbose_name = _('supersense revision')


# You must register the model here

admin.site.register(Metadata)
admin.site.register(Supersense)
