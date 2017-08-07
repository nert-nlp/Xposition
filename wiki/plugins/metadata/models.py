from django.core.urlresolvers import reverse
from django.db import models
import copy
from django.utils.encoding import force_text
from django.contrib.contenttypes.models import ContentType
from functools import reduce
from wiki.models import Article, ArticleRevision
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

    def html(self):
        if self.current_revision:
            return self.current_revision.metadatarevision.html()
        return ''

    def createNewRevision(self, request):
        # Add self.metadatatype check and call the relevant newRevision method on the derived class object
                # USED WHEN AN ARTICLE IS EDITED
        if self.supersense:
            return self.supersense.newRevision(request).current_revision


    class Meta():
        verbose_name = _('metadata')

class MetadataRevision(RevisionPluginRevision):
    template = models.CharField(max_length=100, default="wiki/view.html", editable=False)
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=200)
    articleRevision = models.OneToOneField(ArticleRevision, null=True)

    def __str__(self):
        return ('Metadata Revision: %s %d') % (self.name, self.revision_number)

    def html(self):
        return '<a href="' + self.articleRevision.article.get_absolute_url() + '">' + str(self.name) + '</a>'

    class Meta:
        verbose_name = _('metadata revision')


class Supersense(Metadata):

    def newRevision(self, request):
        revision = SupersenseRevision()
        revision.inherit_predecessor(self)
        revision.deleted = False
        revision.name = copy.deepcopy(self.current_revision.metadatarevision.supersenserevision.name)
        revision.description = copy.deepcopy(self.current_revision.metadatarevision.supersenserevision.description)
        revision.animacy = copy.deepcopy(self.current_revision.metadatarevision.supersenserevision.animacy)
        revision.counterpart = copy.deepcopy(self.current_revision.metadatarevision.supersenserevision.counterpart)
        revision.template = "supersense_article_view.html"
        revision.set_from_request(request)
        self.add_revision(revision)
        return self


    def setCounterpart(self, newCounterpart):
        revision = self.current_revision
        oldCounterpart = self.current_revision.counterpart

        if newCounterpart is not oldCounterpart:
            self.current_revision.counterpart = newCounterpart
            self.current_revision.save()
        return self


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


class Usage(Metadata):

    def __str__(self):
        if self.current_revision:
            return self.current_revision.metadatarevision.name
        else:
            return ugettext('Current revision not set!!')
    class Meta:
        verbose_name = _('usage')

class UsageRevision(MetadataRevision):

    role = models.ForeignKey(Supersense, null=True, related_name='role')
    function = models.ForeignKey(Supersense, null=True, related_name='function')

    def __str__(self):
        return ('Usage Revision: %s %d') % (self.name, self.revision_number)

    class Meta:
        verbose_name = _('usage revision')


class Example(models.Model):
    exampleString = models.CharField(max_length=200)


class Adposition(Metadata):

    def __str__(self):
        if self.current_revision:
            return self.current_revision.metadatarevision.name
        else:
            return ugettext('Current revision not set!!')
    class Meta:
        verbose_name = _('adposition')

class AdpositionRevision(MetadataRevision):

    def __str__(self):
        return ('Adposition Revision: %s %d') % (self.name, self.revision_number)

    class Meta:
        verbose_name = _('adposition revision')


# You must register the model here

admin.site.register(Supersense)
admin.site.register(SupersenseRevision)
admin.site.register(Usage)
admin.site.register(UsageRevision)
admin.site.register(Example)
admin.site.register(Adposition)
admin.site.register(AdpositionRevision)
