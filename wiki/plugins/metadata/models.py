from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.core.validators import RegexValidator
from django.db import models
from bitfield import BitField
import copy, sys, re
from enum import IntEnum
from django.utils.encoding import force_text
from django.contrib.contenttypes.models import ContentType
from functools import reduce
from wiki.models import Article, ArticleRevision
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext
from django.contrib import admin
from django.db.models.signals import pre_save, post_save
from wiki.decorators import disable_signal_for_loaddata
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

class MetaEnum(IntEnum):
    """Base class for an enum defining choices for an integer model field."""
    @classmethod
    def choices(cls):
        """For use with e.g. PositiveIntegerField"""
        return [(m.value, m.name.replace('_', ' ')) for m in cls]
    @classmethod
    def flags(cls):
        """For use with BitField"""
        return [(m.name, m.name.replace('_', ' ')) for m in cls]

# These are the different metadata models. Extend from the base metadata class if you want to add a
# new metadata type. Make sure to register your model below.

class SimpleMetadata(ArticlePlugin):
    """Metadata without revision tracking."""
    @property
    def template(self):
        a = self.article
        u = dir(a)
        if deepest_instance(self)!=self:
            return deepest_instance(self).template
        elif self.article.urlpath_set.filter(slug='supersenses'):
            return 'supersense_list.html'
        elif self.article.urlpath_set.filter(slug='construals'):
            return 'construal_list.html'

    def html(self):
        return '<a href="' + self.article.get_absolute_url() + '">' + str(self) + '</a>'

@disable_signal_for_loaddata
def on_article_revision_post_save(**kwargs):
    article = kwargs['instance']
    articleplugins = [deepest_instance(z) for z in article.articleplugin_set.all()]
    metadata = [z for z in articleplugins if isinstance(z, Metadata)]   # not SimpleMetadata, because it won't have revisions to link to!
    assert 0<=len(metadata)<=1
    if metadata:
        metadata = metadata[0]
        article_current_revision = article.current_revision
        try:
            article_current_revision.metadata_revision
        except ArticleRevision.metadata_revision.RelatedObjectDoesNotExist:
            # create a new metadata revision to accompany the new article revision,
            # so the relation is 1-to-1
            metadata.link_current_to_article_revision(article_revision=article_current_revision, commit=True)
            x = deepest_instance(metadata.current_revision)

post_save.connect(on_article_revision_post_save, Article)

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

    # def createNewRevision(self, request):
    #     # Add self.metadatatype check and call the relevant newRevision method on the derived class object
    #             # USED WHEN AN ARTICLE IS EDITED
    #     if self.supersense:
    #         return self.supersense.newRevision(request).current_revision

    def add_revision(self, newrevision, request, article_revision=None, save=True):
        """
        Given a revision to make to the metadata, save it,
        and create a new article revision so they are in parallel unless one is provided.
        If an article revision is provided, then link the metadata revision to it;
        otherwise, initially save metadata_revision.article_revision as null
        (the signal triggered by the new article revision being saved will lead to this
        method being called again with the article_revision).
        """

        if article_revision is None:
            # first save the submitted metadata. article_revision will be null
            super(Metadata, self).add_revision(newrevision, save=save)

            # create article revision
            article_revision = ArticleRevision()
            article_revision.inherit_predecessor(self.article)
            article_revision.set_from_request(request)
            article_revision.automatic_log = newrevision.automatic_log
            self.article.add_revision(article_revision, save=save)
            # will trigger the on_article_revision_pre_save signal handler,
            # which calls this method again, supplying an article_revision
        else:
            # update the metadata revision so it is attached to an article_revision
            newrevision.article = self.article  # defined in ArticlePlugin, which SimplePlugin and RevisionPlugin both inherit from
            newrevision.article_revision = article_revision

            super(Metadata, self).add_revision(newrevision, save=save)

    def newRevision(self, request, article_revision=None, commit=True, **changes):
        """Create a new revision either because an edit has been made
        to the metadata, or because an edit has been made to article content."""

        x = [str(deepest_instance(r)) for r in self.revision_set.all()]
        curr = deepest_instance(self.current_revision)
        revision = type(curr)()
        revision.inherit_predecessor(self)
        revision.deleted = False
        fields = self.field_names()
        for fld in fields:
            if fld in changes and changes[fld]==getattr(curr, fld):
                del changes[fld]    # actually no change to this field
            if fld not in changes:
                setattr(revision, fld, copy.deepcopy(getattr(curr, fld)))
            else:
                setattr(revision, fld, changes[fld])

        keydiff = changes.keys() & fields
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
            revision.set_from_request(request)
            revision.automatic_log = ' • '.join(f'{f.title()}: {old} → {new}' for f,(old,new) in hchanges.items())
        if keydiff or article_revision:
            self.add_revision(revision, request, article_revision=article_revision, save=commit)
        return self

    def link_current_to_article_revision(self, article_revision, commit=True):
        """
        Called whenever an article has been saved.
        If that article's saving was triggered by a user edit to metadata,
        we link the new metadata revision to the new article revision.
        If it was triggered by a user edit to the article,
        we create a new metadata revision and pass the article revision
        so they will be linked.

        N.B. The metadata current_revision pointer is not adjusted
        when an article is reverted to a previous version.
        This means that though the correct version of metadata will be displayed
        (by following the article_revision.metadata_revision pointer),
        code such as the editsupersense form that relies on
        Metadata.current_revision will be led astray.
        """
        curr = deepest_instance(self.current_revision)
        if curr.article_revision is not None:
            # we need to create a new metadata revision to match the new article revision!
            self.newRevision(request=None, article_revision=article_revision, commit=commit)
            curr = deepest_instance(self.current_revision)
            assert curr.article_revision is not None
            # it was linked in newRevision
        else:
            curr.article_revision = article_revision
            if commit:
                curr.save()

    @property
    def template(self):
        if deepest_instance(self)!=self:
            return deepest_instance(self).template

    class Meta():
        verbose_name = _('metadata')
		# issue #10: alphabetize models
        ordering = ['current_revision__metadatarevision__name']




class MetadataRevision(RevisionPluginRevision):
    template = models.CharField(max_length=100, default="wiki/view.html", editable=False)
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=200)
    article_revision = models.OneToOneField(ArticleRevision, null=True, related_name='metadata_revision')

    unique_together = None  # can be overriden by subclasses

    def __str__(self):
        return ('Metadata Revision: %s %d') % (self.name, self.revision_number)

    def html(self):
        return '<a href="' + self.plugin.article.get_absolute_url() + '">' + str(self.name) + '</a>'

    def validate_unique(self, exclude=None):
        """
        Implement unique_together checks which cannot be listed under Meta
        and implemented at the database level because they contain fields
        from the superclass, which is a different database table under
        multi-table inheritance
        """

        if self.unique_together:
            # revision_number is not incremented yet. pretend that it is for uniqueness check
            if self.revision_number is None:
                self.revision_number = 0
            unique_checks = [(type(self), group) for group in self.unique_together]
            errors = self._perform_unique_checks(unique_checks)
            if errors:
                raise ValidationError(errors)
            # undo our temporary revision_number
            if self.revision_number==0:
                self.revision_number = None

        return super(MetadataRevision, self).validate_unique(exclude=exclude)

    class Meta:
        verbose_name = _('metadata revision')


class Supersense(Metadata):
    category = models.ForeignKey(ArticleCategory, null=False, related_name='supersense')

    def field_names(self):
        return {'name', 'description', 'parent', 'animacy'}

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
    class AnimacyType(MetaEnum):
        unspecified = 0
        animate = 1

    animacy = models.PositiveIntegerField(choices=AnimacyType.choices(), default=AnimacyType.unspecified)
    parent = models.ForeignKey(Supersense, null=True, blank=True, related_name='sschildren')

    unique_together = [('name', 'revision_number')]

    def __str__(self):
        return ('Supersense Revision: %s %d') % (self.name, self.revision_number)

    @classmethod
    def editurl(cls, urlpath):
        return reverse('wiki:metadata_edit_supersense', args=[urlpath])

    @property
    def supersense(self):
        return Supersense.objects.get(current_revision = self)

    """ # TODO: this is actually a field in ArticlePlugin. let's make sure to set it!
    @property
    def article(self):
        return self.supersense.article
    """

    class Meta:
        verbose_name = _('supersense revision')


class Construal(SimpleMetadata):

    role = models.ForeignKey(Supersense, null=True, related_name='rfs_with_role')
    function = models.ForeignKey(Supersense, null=True, related_name='rfs_with_function')

    def __str__(self):
        return str(self.role)+' ~> '+str(self.function)

    @property
    def template(self):
        return "construal_article_view.html"

    class Meta:
        verbose_name = _('construal')
        unique_together = ('role', 'function')
		# issue #10: alphabetize models
        ordering = ['role', 'function']

class Case(MetaEnum):
    """Inventory of cases based on UniMorph <http://unimorph.org/>"""
    Unknown = UNK = 1

    # Core cases
    # Nominative-Accusative alignment
    Nominative = NOM = 2**1
    Accusative = ACC = 2**2
    # Ergative-Absolutive alignment
    Ergative = ERG = 2**3
    Absolutive = ABS = 2**4
    # Tripartite alignment
    NominativeSOnly = NOMS = 2**5

    # Non-core, non-local cases
    Dative = DAT = 2**6
    Benefactive = BEN = 2**7
    Purposive = PRP = 2**8
    Genitive = GEN = 2**9
    Relative = REL = 2**10
    Partitive = PRT = 2**11
    Instrumental = INS = 2**12
    Comitative = COM = 2**13
    Vocative = VOC = 2**14
    Comparative = COMPV = 2**15
    Equative = EQTV = 2**16
    Privative = PRIV = 2**17
    Proprietive = PROPR = 2**18
    Aversive = AVR = 2**19
    Formal = FRML = 2**20
    Translative = TRANS = 2**21
    EssiveModal = BYWAY = 2**22

    # Local cases
    # excluding Place cases
    # Distal
    Distal = REM = 2**23
    Proximate = PROX = 2**24
    # Motion
    Essive = ESS = 2**25
    Allative = ALL = 2**26
    Ablative = ABL = 2**27
    # Aspect
    Approximative = APPRX = 2**28
    Terminative = TERM = 2**29

    @classmethod
    def longname(cls, val):
        return val.name
    @classmethod
    def shortname(cls, val):
        val = cls(val)
        return [k for k,v in cls.__members__.items() if v is val and k.isupper()][0]


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

    slug = models.CharField(max_length=20, unique=True,
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

    class Presence(MetaEnum):
        none = 1
        some = 2
        primary_or_sole_type = 3

    pre = models.PositiveIntegerField(choices=Presence.choices(), verbose_name="Prepositions/case prefixes or proclitics?")
    post = models.PositiveIntegerField(choices=Presence.choices(), verbose_name="Postpositions/case suffixes or enclitics?")
    circum = models.PositiveIntegerField(choices=Presence.choices(), verbose_name="Circumpositions/case circumfixes?")
    separate_word = models.PositiveIntegerField(choices=Presence.choices(), verbose_name="Adpositions/overt case markers can be separate words?")
    clitic_or_affix = models.PositiveIntegerField(choices=Presence.choices(), verbose_name="Adpositions/overt case markers can be clitics or affixes?")

    # Maybe also: Does adposition/case morpheme ever encode other features,
    # like definiteness? Is there differential case marking?
    # Do all adpositions assign the same case? Which kinds of adpositions inflect e.g. for pronouns?

    #exclude_supersenses = models.ManyToManyField(Supersense, related_name="not_in_language", blank=True)

    class CaseSystemType(MetaEnum):
        none = 1
        pronominal = 2
        nominal = 3

    case_for = models.PositiveIntegerField(choices=CaseSystemType.choices(), verbose_name="Does the language have (affixal) case on nouns and pronouns, just pronouns, or neither?")
    cases = BitField(flags=Case.flags(), verbose_name="All cases present in the language")
    pobj_cases = BitField(flags=Case.flags(), verbose_name="All cases that ever apply to an adpositional object")

    @classmethod
    def with_nav_links(cls):
        return cls.objects.filter(navlink=True)

    def __str__(self):
        return self.name

    def morph_types(self):
        options = []
        default = None
        NONE = self.Presence.none

        if self.separate_word!=NONE:
            if self.pre!=NONE: options.append(Adposition.MorphType.from_properties('separate_word','pre'))
            if self.post!=NONE: options.append(Adposition.MorphType.from_properties('separate_word','post'))
            if self.circum!=NONE: options.append(Adposition.MorphType.from_properties('separate_word','circum'))
        if self.clitic_or_affix!=NONE:
            if self.pre!=NONE: options.append(Adposition.MorphType.from_properties('clitic_or_affix','pre'))
            if self.post!=NONE: options.append(Adposition.MorphType.from_properties('clitic_or_affix','post'))
            if self.circum!=NONE: options.append(Adposition.MorphType.from_properties('clitic_or_affix','circum'))

        if self.separate_word>self.clitic_or_affix:
            default_attachment = 'separate_word'
        elif self.separate_word<self.clitic_or_affix:
            default_attachment = 'clitic_or_affix'
        else:
            default_attachment = None

        default_position = max({'pre': self.pre, 'post': self.post, 'circum': self.circum}.items(), key=lambda x: x[1])
        if sum(1 for x in {self.pre,self.post,self.circum} if x==default_position[1])>1:
            default_position = None # e.g., two "some" values but no "primary or sole" value
        else:
            default_position = default_position[0]

        if default_attachment and default_position:
            default = Adposition.MorphType.from_properties(default_attachment, default_position)

        return options, default

    @property
    def template(self):
        return "language_article_view.html"

    @classmethod
    def editurl(cls, urlpath):
        #return "_plugin/metadata/editlang"
        return reverse('wiki:metadata_edit_language', args=[urlpath])

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

    class MorphType(MetaEnum):
        standalone_preposition = 1
        standalone_postposition = 2
        standalone_circumposition = 3
        prefix = 4
        suffix = 5
        circumfix = 6

        @classmethod
        def from_properties(cls, attachment=None, position=None):
            props2type = {('separate_word','pre'): cls.standalone_preposition,
                          ('separate_word','post'): cls.standalone_postposition,
                          ('separate_word','circum'): cls.standalone_circumposition,
                          ('clitic_or_affix','pre'): cls.prefix,
                          ('clitic_or_affix','post'): cls.suffix,
                          ('clitic_or_affix','circum'): cls.circumfix}
            if attachment is None or position is None:
                return props2type
            return props2type[attachment,position]

    class Transitivity(MetaEnum):
        always_intransitive = 0
        sometimes_transitive = 1
        always_transitive = 2


    def field_names(self):
<<<<<<< HEAD
        return {'name', 'transliteration', 'other_forms', 'description', 'lang', 'morphtype', 'transitivity', 'obj_cases'} 
=======
		# issue #4: transliteration field
        return {'name', 'transliteration', 'other_forms', 'description', 'lang', 'morphtype', 'transitivity', 'obj_cases'}
>>>>>>> master

    def __str__(self):
        if self.current_revision:
            return self.current_revision.metadatarevision.name
        else:
            return ugettext('Current revision not set!!')

    @property
    def template(self):
        return "adposition_article_view.html"

    class Meta:
        verbose_name = _('adposition')


class AdpositionRevision(MetadataRevision):

    lang = models.ForeignKey(Language, related_name='adpositionrevisions', verbose_name='Language/dialect')
    # name = models.CharField(max_length=200, verbose_name='Lemma',
    #     help_text="Lowercase unless it would normally be capitalized in a dictionary")
<<<<<<< HEAD
    transliteration = models.CharField(max_length=200, blank=True, verbose_name="Transliteration",
        help_text="Pronunciation written in alphabetic letters (optional)")
=======
	# issue #4: transliteration field
    transliteration = models.CharField(max_length=200, blank=True, verbose_name="Transliteration",
        help_text="Romanization/phonemic spelling")
>>>>>>> master
    other_forms = models.CharField(max_length=200, blank=True, verbose_name="Other spellings or inflections",
        help_text="Exclude typos")
    morphtype = models.PositiveIntegerField(choices=Adposition.MorphType.choices(), verbose_name="Morphological type")
    transitivity = models.PositiveIntegerField(choices=Adposition.Transitivity.choices())
    obj_cases = BitField(flags=Case.flags(), verbose_name="Possible cases of the object")

    unique_together = [('name', 'lang', 'revision_number')]

    def __str__(self):
        return ('Adposition Revision: %s %d') % (self.name, self.revision_number)

    @classmethod
    def editurl(cls, urlpath):
        #return "_plugin/metadata/editp"
        return reverse('wiki:metadata_edit_adposition', args=[urlpath])

    @property
    def adposition(self):
        return Adposition.objects.get(current_revision = self)

    class Meta:
        verbose_name = _('adposition revision')

class Usage(Metadata):

    def __str__(self):
        if self.current_revision:
            return self.current_revision.metadatarevision.name
        else:
            return ugettext('Current revision not set!!')

    def field_names(self):
        return {'name', 'description', 'adposition', 'obj_case', 'construal'}

    @property
    def template(self):
        return "usage_article_view.html"

    class Meta:
        verbose_name = _('usage')


class UsageRevision(MetadataRevision):

    adposition = models.ForeignKey(Adposition, null=True, related_name='usages')
    obj_case = models.PositiveIntegerField(choices=Case.choices(), null=True)
    construal = models.ForeignKey(Construal, null=True, related_name='usages')

    unique_together = [('adposition', 'obj_case', 'construal', 'revision_number')]

    def __str__(self):
        return ('Usage Revision: %s %d') % (self.name, self.revision_number)



    class Meta:
        verbose_name = _('usage revision')
		# issue #10: alphabetize models
        ordering = ['adposition', 'construal']


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
admin.site.register(Language)
admin.site.register(Corpus)
admin.site.register(Adposition)
admin.site.register(AdpositionRevision)
admin.site.register(Usage)
admin.site.register(UsageRevision)
admin.site.register(Example)
admin.site.register(ExampleRevision)
