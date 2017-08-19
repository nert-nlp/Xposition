from django.core.urlresolvers import reverse
from django.core.validators import RegexValidator
from django.db import models
import copy, sys, re
from django.utils.encoding import force_text
from django.contrib.contenttypes.models import ContentType
from functools import reduce
from wiki.models import Article, ArticleRevision
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext
from django.contrib import admin
from wiki.plugins.categories.models import ArticleCategory
from wiki.models.pluginbase import ArticlePlugin, RevisionPlugin, RevisionPluginRevision
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

class SimpleMetadata(ArticlePlugin):
    """Metadata without revision tracking."""
    @property
    def template(self):
        if deepest_instance(self)!=self:
            return deepest_instance(self).template


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

    @property
    def template(self):
        if deepest_instance(self)!=self:
            return deepest_instance(self).template

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
    category = models.ForeignKey(ArticleCategory, null=False, related_name='supersense')

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

    @property
    def template(self):
        return "supersense_article_view.html"

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


class Construal(Metadata):

    def __str__(self):
        if self.current_revision:
            return self.current_revision.metadatarevision.name
        else:
            return ugettext('Current revision not set!!')
    class Meta:
        verbose_name = _('construal')

class ConstrualRevision(MetadataRevision):

    role = models.ForeignKey(Supersense, null=True, related_name='rfs_with_role')
    function = models.ForeignKey(Supersense, null=True, related_name='rfs_with_function')

    def __str__(self):
        return ('Construal Revision: %s %d') % (self.name, self.revision_number)

    class Meta:
        verbose_name = _('construal revision')

lang_code_validator = RegexValidator(r'^[a-z]+(-?[a-z]+)*$',
    message="Language code should consist of lowercase ASCII strings separated by hyphens")

class Language(SimpleMetadata):
    """
    A language, language family, or dialect.
    The slug should be an ISO language code (2-digit if possible)
    for languages and dialects, but this is not enforced.
    Associated with an ArticleCategory, but metadata revisions are not tracked.
    Genetic relationships can be reflected in the category inheritance structure.
    """

    name = models.CharField(max_length=200,
        help_text="Basic name, e.g. <tt>English</tt>")

    slug = models.CharField(max_length=20,
        help_text="Short (typically 2-character ISO) code for the language/dialect, "
                  "such as <tt>en</tt> for English and <tt>en-us</tt> for American English.",
        validators=[lang_code_validator])

    category = models.ForeignKey(ArticleCategory, null=False, related_name='language')

    # Other names for the language/dialect, possibly in other orthographies
    other_names = models.CharField(max_length=200, blank=True, verbose_name="Other names for the language/dialect")

    wals_url = models.URLField(max_length=200, blank=True, verbose_name="WALS URL",
    help_text="World Atlas of Linguistic Structures entry listed on "
              "<a href='http://wals.info/languoid'>this page</a>, e.g. "
              "<tt>http://wals.info/languoid/lect/wals_code_heb</tt>")

    # Writing direction: LTR or RTL?
    rtl = models.BooleanField(default=False, verbose_name="Right-to-left language?")

    # Should the language be featured with a navigation link
    # on the main menu?
    navlink = models.BooleanField(default=False)

    # Linguistic characterization of adpositions/case marking in the language.
    # This probably needs some work.


    PRESENCE = (
        (1, 'none'),
        (2, 'some'),
        (3, 'primary or sole type')
    )
    pre = models.PositiveIntegerField(choices=PRESENCE, verbose_name="Prepositions/case prefixes or proclitics?")
    post = models.PositiveIntegerField(choices=PRESENCE, verbose_name="Postpositions/case suffixes or enclitics?")
    circum = models.PositiveIntegerField(choices=PRESENCE, verbose_name="Circumpositions/case circumfixes?")
    separate_word = models.PositiveIntegerField(choices=PRESENCE, verbose_name="Adpositions/overt case markers can be separate words?")
    clitic_or_affix = models.PositiveIntegerField(choices=PRESENCE, verbose_name="Adpositions/overt case markers can be clitics or affixes?")

    # Maybe also: Does adposition/case morpheme ever encode other features,
    # like definiteness? Is there differential case marking?
    # Do all adpositions assign the same case? Which kinds of adpositions inflect e.g. for pronouns?

    #exclude_supersenses = models.ManyToManyField(Supersense, related_name="not_in_language", blank=True)

    @classmethod
    def with_nav_links(cls):
        return cls.objects.filter(navlink=True)

    def __str__(self):
        return self.name

    @property
    def template(self):
        return "language_article_view.html"

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
    construal = models.ForeignKey(Construal, null=True, related_name='usages')

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
    usage = models.ForeignKey(Construal, null=True, related_name='examples')

    def __str__(self):
        return ('Example Revision: %s %d') % (self.name, self.revision_number)

    class Meta:
        verbose_name = _('example revision')

# You must register the model here

admin.site.register(Supersense)
admin.site.register(SupersenseRevision)
admin.site.register(Construal)
admin.site.register(ConstrualRevision)
admin.site.register(Language)
admin.site.register(Corpus)
admin.site.register(Adposition)
admin.site.register(AdpositionRevision)
admin.site.register(Usage)
admin.site.register(UsageRevision)
admin.site.register(Example)
admin.site.register(ExampleRevision)
