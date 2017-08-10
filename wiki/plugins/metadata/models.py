from django.core.urlresolvers import reverse
from django.db import models
import copy, sys
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

def deepest_instance(x):
    """
    Simulate true inheritance given an instance of
    an object that uses multi-table inheritance.
    E.g., if Z is a subclass of Y which is a subclass of X,
    instantiating a Z() will result in an X whose .y is a Y, whose .z is a Z.
    deepest_instance(x) returns x.y.z.
    This is only necessary to access a database field defined by Z
    (methods inherit normally).
    """
    inst = x
    typ = type(x)
    #s = str(inst)
    while inst:
        # list the subclasses of 'typ' which are instantiated as attributes of 'inst'
        sub = [cls for cls in typ.__subclasses__() if hasattr(inst, cls.__name__.lower())]
        if not sub:
            break
        typ = sub[0]
        # dot into the corresponding attribute of the instance
        inst = getattr(inst, typ.__name__.lower())
        #s += '.' + y.__name__.lower()
    return inst


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
    #articleRevision = models.OneToOneField(ArticleRevision, null=True) # TODO: is this even used?

    def __str__(self):
        return ('Metadata Revision: %s %d') % (self.name, self.revision_number)

    def html(self):
        return '<a href="' + self.plugin.article.get_absolute_url() + '">' + str(self.name) + '</a>'

    class Meta:
        verbose_name = _('metadata revision')


class Supersense(Metadata):


    def newRevision(self, request, recursive=False, **changes):
        revision = SupersenseRevision()
        revision.inherit_predecessor(self)
        revision.deleted = False
        curr = deepest_instance(self.current_revision)
        for fld in ('name', 'description', 'animacy'):
            if fld in changes and changes[fld]==getattr(curr, fld):
                del changes[fld]    # actually no change to this field
            if fld not in changes:
                setattr(revision, fld, copy.deepcopy(getattr(curr, fld)))
            else:
                setattr(revision, fld, changes[fld])
        if 'counterpart' in changes:
            if changes['counterpart']==curr.counterpart:
                del changes['counterpart']
            elif not recursive:
                print(f'{changes["counterpart"]} ({id(changes["counterpart"])}) is not {curr.counterpart} ({id(curr.counterpart)})')
                print(f'in {self}, setting counterpart to {changes["counterpart"]} recursively', file=sys.stderr)
                revision.counterpart = self.updateCounterpart(changes['counterpart'], request)
            else:
                print(f'{changes["counterpart"]} is not {curr.counterpart}')
                print(f'in {self}, setting counterpart to {changes["counterpart"]} nonrecursively', file=sys.stderr)
                revision.counterpart = changes['counterpart']

        if changes.keys() & {'name', 'description', 'animacy', 'counterpart'}:
            revision.template = "supersense_article_view.html"
            revision.set_from_request(request)
            revision.automatic_log = repr({f: v for f,v in changes.items() if f in {'name','description','animacy'}})  # TODO: make HTML
            #revision.articleRevision = # TODO: do we need to set this?
            self.add_revision(revision)
            curr2 = deepest_instance(self.current_revision)
            print(f'in {self}, counterpart is now {curr2.counterpart}', file=sys.stderr)
        return self

    def updateCounterpart(self, ss2, request):
        """Orchestrates new revisions required for changing a counterpart link between two supersenses"""
        ss1curr = deepest_instance(self.current_revision)
        if ss1curr.counterpart:
            print(f"{ss1curr}'s current counterpart {ss1curr.counterpart}: changing its counterpart from {deepest_instance(ss1curr.counterpart.current_revision).counterpart}", file=sys.stderr)
            ss1curr.counterpart.newRevision(request, counterpart=None, recursive=True)  # unset counterpart
            print(f"{ss1curr}'s counterpart {ss1curr.counterpart}'s counterpart changed to {deepest_instance(ss1curr.counterpart.current_revision).counterpart}", file=sys.stderr)
        if ss2:
            ss2curr = deepest_instance(ss2.current_revision)
            if ss2curr.counterpart:
                print(f"{ss2curr}'s current counterpart {ss2curr.counterpart}: changing its counterpart from {deepest_instance(ss2curr.counterpart.current_revision).counterpart}", file=sys.stderr)
                ss2curr.counterpart.newRevision(request, counterpart=None, recursive=True)  # unset counterpart
                print(f"{ss2curr}'s counterpart {ss2curr.counterpart}'s counterpart changed to {deepest_instance(ss2curr.counterpart.current_revision).counterpart}", file=sys.stderr)
        ss2.newRevision(request, counterpart=self, recursive=True)
        return ss2

    def __setCounterpart(self, newCounterpart):
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
