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
from wiki.models import Category
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

    def add_revision(self, newrevision, request):
        """Given a revision to make to the metadata, create a corresponding article revision"""
        arevision = ArticleRevision()
        arevision.inherit_predecessor(self.article)
        arevision.set_from_request(request)
        arevision.automatic_log = newrevision.automatic_log
        self.article.add_revision(arevision)
        super(Metadata, self).add_revision(newrevision)

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
    category = models.ForeignKey(Category, null=False)

    def newRevision(self, request, recursive=False, **changes):
        revision = SupersenseRevision()
        revision.inherit_predecessor(self)
        revision.deleted = False
        curr = deepest_instance(self.current_revision)
        for fld in ('name', 'description', 'parent', 'animacy'):
            if fld in changes and changes[fld]==getattr(curr, fld):
                del changes[fld]    # actually no change to this field
            if fld not in changes:
                setattr(revision, fld, copy.deepcopy(getattr(curr, fld)))
            else:
                setattr(revision, fld, changes[fld])

        keydiff = changes.keys() & {'name', 'description', 'parent', 'animacy'}
        if keydiff:
            hchanges = {}   # human-readable (old,new) pairs for log message
            for f in keydiff:
                # raw values
                old = getattr(deepest_instance(self.current_revision), f)
                new = changes[f]
                # convert to human-readable if applicable
                fld = type(curr)._meta.get_field(f)
                if fld.choices:
                    choices = dict(fld.choices)
                    old = choices[int(old)]
                    new = choices[int(new)]
                hchanges[f] = (old, new)
            revision.template = "supersense_article_view.html"
            revision.set_from_request(request)
            revision.automatic_log = ' • '.join(f'{f.title()}: {old} → {new}' for f,(old,new) in hchanges.items())
            self.add_revision(revision, request)
            curr2 = deepest_instance(self.current_revision)
        return self

    def __str__(self):
        if self.current_revision:
            return self.current_revision.metadatarevision.name
        else:
            return ugettext('Current revision not set!!')


    class Meta:
        verbose_name = _('supersense')

class SupersenseRevision(MetadataRevision):
    ANIMACY_TYPES = (
        (0, 'unspecified'),
        (1, 'animate'),
    )
    animacy = models.PositiveIntegerField(choices=ANIMACY_TYPES, default=0)
    parent = models.ForeignKey(Supersense, null=True, blank=True, related_name='sschildren')

    def __str__(self):
        return ('Supersense Revision: %s %d') % (self.name, self.revision_number)

    class Meta:
        verbose_name = _('supersense revision')


class RoleFunction(Metadata):

    def __str__(self):
        if self.current_revision:
            return self.current_revision.metadatarevision.name
        else:
            return ugettext('Current revision not set!!')
    class Meta:
        verbose_name = _('rolefunction')

class RoleFunctionRevision(MetadataRevision):

    role = models.ForeignKey(Supersense, null=True, related_name='rfs_with_role')
    function = models.ForeignKey(Supersense, null=True, related_name='rfs_with_function')

    def __str__(self):
        return ('RoleFunction Revision: %s %d') % (self.name, self.revision_number)

    class Meta:
        verbose_name = _('rolefunction revision')

class Language(Metadata):

    def __str__(self):
        if self.current_revision:
            return self.current_revision.metadatarevision.name
        else:
            return ugettext('Current revision not set!!')
    class Meta:
        verbose_name = _('language')

class Corpus(Metadata):

    def __str__(self):
        if self.current_revision:
            return self.current_revision.metadatarevision.name
        else:
            return ugettext('Current revision not set!!')
    class Meta:
        verbose_name = _('corpus')

class Adposition(Metadata):
    lang = models.ForeignKey(Language, null=True, related_name='adpositions')

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

class Usage(Metadata):

    def __str__(self):
        if self.current_revision:
            return self.current_revision.metadatarevision.name
        else:
            return ugettext('Current revision not set!!')
    class Meta:
        verbose_name = _('usage')

class UsageRevision(MetadataRevision):

    adposition = models.ForeignKey(Adposition, null=True, related_name='usages')
    rolefunction = models.ForeignKey(RoleFunction, null=True, related_name='usages')

    def __str__(self):
        return ('Usage Revision: %s %d') % (self.name, self.revision_number)

    class Meta:
        verbose_name = _('usage revision')

class Example(models.Model):

    def __str__(self):
        if self.current_revision:
            return self.current_revision.metadatarevision.name
        else:
            return ugettext('Current revision not set!!')
    class Meta:
        verbose_name = _('example')

class ExampleRevision(MetadataRevision):
    exampleXML = models.CharField(max_length=200)
    usage = models.ForeignKey(RoleFunction, null=True, related_name='examples')

    def __str__(self):
        return ('Example Revision: %s %d') % (self.name, self.revision_number)

    class Meta:
        verbose_name = _('example revision')

# You must register the model here

admin.site.register(Supersense)
admin.site.register(SupersenseRevision)
admin.site.register(RoleFunction)
admin.site.register(RoleFunctionRevision)
admin.site.register(Language)
admin.site.register(Corpus)
admin.site.register(Adposition)
admin.site.register(AdpositionRevision)
admin.site.register(Usage)
admin.site.register(UsageRevision)
admin.site.register(Example)
admin.site.register(ExampleRevision)
