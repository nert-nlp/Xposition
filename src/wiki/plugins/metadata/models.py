from django.core.exceptions import ValidationError
from django.urls import reverse
from django.core.validators import RegexValidator
from django.utils.html import conditional_escape, format_html, mark_safe
from django.db import models

from bitfield import BitField
import copy, sys, re, urllib
from enum import IntEnum
from django.utils.encoding import force_text
from django.utils.functional import cached_property
from django.utils.safestring import mark_safe
from django.contrib.contenttypes.models import ContentType
from functools import reduce
from wiki.models import Article, ArticleRevision
from django.utils.translation import ugettext_lazy as _
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext
from django.contrib import admin
from django.db.models.signals import pre_save, post_save
from wiki.core.markdown import article_markdown
from wiki.decorators import disable_signal_for_loaddata
from categories.models import ArticleCategory

from wiki.models.pluginbase import ArticlePlugin, RevisionPlugin, RevisionPluginRevision
from django.core.exceptions import ObjectDoesNotExist


try:
    from django.contrib.contenttypes.fields import GenericForeignKey
except ImportError:
    from django.contrib.contenttypes.generic import GenericForeignKey
from django.core.files.storage import get_storage_class

from django.utils.translation import ugettext_lazy as _

class StringList(list):
    '''
    List of values stored as space-separated strings.
    With a custom __str__, providing an instance of this class as a field value
    ensures that it will be rendered correctly in form fields.
    '''
    def __str__(self):
        return ' '.join(map(str, self))

    @staticmethod
    def from_str(s):
        return StringList(s.strip().split())

# cf. SeparatedValuesField at https://stackoverflow.com/a/1113039
class StringListField(models.TextField):
    def to_python(self, value):
        '''Deserialize a value into a Python-friendly object.'''
        if not value: return
        if isinstance(value, list):
            return value
        return StringList.from_str(str(value))

    def from_db_value(self, value, expression, connection, context=None):
        return self.to_python(value)

    def get_db_prep_value(self, value, connection=None, prepared=True, **kwargs):
        if not value: return ""
        if not isinstance(value, (list, tuple)):
            value = self.to_python(value)
        return str(StringList(value))

    def value_to_string(self, obj):
        value = self._get_val_from_obj(obj)
        return self.get_db_prep_value(value)

# here for migrations
class SeparatedValuesField(StringListField):
    ...

class IntListField(StringListField):
    def to_python(self, value):
        sl = super(IntListField, self).to_python(value)
        for i in range(len(sl)):
            sl[i] = int(sl[i])
        return sl

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
    # s = str(inst)
    while inst:
        # list the subclasses of 'typ' which are instantiated as attributes of 'inst'
        sub = [cls for cls in typ.__subclasses__() if hasattr(inst, cls.__name__.lower())]
        if not sub:
            break
        typ = sub[0]
        # dot into the corresponding attribute of the instance
        inst = getattr(inst, typ.__name__.lower())
        # s += '.' + y.__name__.lower()
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
        if deepest_instance(self) != self:
            return deepest_instance(self).template
        elif self.article.urlpath_set.filter(slug='supersenses'):
            return 'supersense_list.html'
        elif self.article.urlpath_set.filter(slug='construals'):
            return 'construal_list.html'

    def html(self):
        di = deepest_instance(self)
        return mark_safe(
            '<a href="' + self.article.get_absolute_url() + '" class="' + type(di).__name__.lower() + '">' + str(
                self) + '</a>')


@disable_signal_for_loaddata
def on_article_revision_post_save(**kwargs):
    article = kwargs['instance']
    articleplugins = [deepest_instance(z) for z in article.articleplugin_set.all()]
    metadata = [z for z in articleplugins if
                isinstance(z, Metadata)]  # not SimpleMetadata, because it won't have revisions to link to!
    assert 0 <= len(metadata) <= 1
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
            di = deepest_instance(self)
            return deepest_instance(self.current_revision).html(container_type=type(di))
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
            if fld in changes and changes[fld] == getattr(curr, fld):
                del changes[fld]  # actually no change to this field
            if fld not in changes:
                setattr(revision, fld, copy.deepcopy(getattr(curr, fld)))
            else:
                setattr(revision, fld, changes[fld])

        keydiff = changes.keys() & fields
        if keydiff:
            hchanges = {}  # human-readable (old,new) pairs for log message
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
            revision.automatic_log = ' • '.join(f'{f.title()}: {old} → {new}' for f, (old, new) in hchanges.items())
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
        if deepest_instance(self) != self:
            return deepest_instance(self).template

    class Meta():
        verbose_name = _('metadata')
        # issue #10: alphabetize models
        ordering = ['current_revision__metadatarevision__name']


class MetadataRevision(RevisionPluginRevision):
    template = models.CharField(max_length=100, default="wiki/view.html", editable=False)
    name = models.CharField(max_length=100, db_index=True)
    description = models.CharField(max_length=300)
    article_revision = models.OneToOneField(ArticleRevision, null=True, related_name='metadata_revision', on_delete=models.CASCADE)

    unique_together = None  # can be overriden by subclasses

    def __str__(self):
        return ('Metadata Revision: %s %d') % (self.name, self.revision_number)

    def html(self, container_type=None):
        kls = ''
        if container_type:
            kls = str(container_type.__name__).lower()
        return mark_safe(
            '<a href="' + self.plugin.article.get_absolute_url() + '" class="' + kls + '">' + str(self.name) + '</a>')

    def descriptionhtml(self):
        return mark_safe(article_markdown(self.description, self.article_revision.article))

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
            if self.revision_number == 0:
                self.revision_number = None

        return super(MetadataRevision, self).validate_unique(exclude=exclude)

    class Meta:
        verbose_name = _('metadata revision')


class Supersense(Metadata):
    category = models.ForeignKey(ArticleCategory, null=False, related_name='supersense', on_delete=models.CASCADE)

    def field_names(self):
        return {'name', 'description', 'parent', 'animacy', 'deprecated', 'deprecation_message'}

    def __str__(self):
        if self.current_revision:
            return self.current_revision.metadatarevision.name
        else:
            return ugettext('Current revision not set!!')

    @cached_property
    def url(self):
        """For effeciency, anything that calls this should call select_related() on the supersense's article__current_revision"""
        # The "correct" way would be self.article.get_absolute_url(), but that is expensive.
        # We take advantage of the fact that a supersense's article title is always the same as its slug.
        return urllib.parse.quote(f'/{self.article}')

    @cached_property
    def html(self):
        """For effeciency, anything that calls this should call .select_related('article__current_revision', 'current_revision__metadatarevision')'"""
        return mark_safe(f'<a href="{self.url}">{self.name_html}</a>')

    @cached_property
    def name_html(self):    # technically this can change if a user edits the supersense name, but it's going to be rare
        cls = "supersense" if not self.current_revision.metadatarevision.supersenserevision.deprecated else "supersense supersense-deprecated"
        return format_html(f'<span class="{cls}">'+'{}</span>', self.current_revision.metadatarevision.name)

    @cached_property
    def template(self):
        return "supersense_article_view.html"

    class Meta:
        verbose_name = _('supersense')


class SupersenseRevision(MetadataRevision):
    class AnimacyType(MetaEnum):
        unspecified = 0
        animate = 1

    animacy = models.PositiveIntegerField(choices=AnimacyType.choices(), default=AnimacyType.unspecified)
    parent = models.ForeignKey(Supersense, null=True, blank=True, related_name='sschildren', on_delete=models.CASCADE)
    deprecated = models.BooleanField(default=False)
    deprecation_message = models.CharField(max_length=250, default='', null=True, blank=True)

    unique_together = [('name', 'revision_number')]

    def __str__(self):
        return ('Supersense Revision: %s %d') % (self.name, self.revision_number)

    @classmethod
    def editurl(cls, urlpath):
        return reverse('wiki:metadata_edit_supersense', args=[urlpath])

    @cached_property
    def supersense(self):
        return Supersense.objects.get(current_revision=self)

    """ # TODO: this is actually a field in ArticlePlugin. let's make sure to set it!
    @property
    def article(self):
        return self.supersense.article
    """

    class Meta:
        verbose_name = _('supersense revision')


class Construal(SimpleMetadata):
    role = models.ForeignKey(Supersense, null=True, blank=True, related_name='rfs_with_role', on_delete=models.CASCADE)
    function = models.ForeignKey(Supersense, null=True, blank=True, related_name='rfs_with_function', on_delete=models.CASCADE)
    special = models.CharField(max_length=200,  default='', null=True, blank=True)

    def __str__(self):
        return str(self.role) + ' ~> ' + str(self.function) if self.function and self.role else str(self.special)

    @cached_property
    def url(self):
        """For efficiency, callers should invoke .select_related('article__current_revision')
        if this field is not already being queried"""
        # The "correct" way would be self.article.get_absolute_url(), but that is expensive.
        # We take advantage of the fact that a construal's article title is always the same as its slug.
        return urllib.parse.quote(f'/{self.article}')    # "??" needs escaping

    @cached_property
    def html(self):
        """For efficiency, callers should invoke .select_related('article__current_revision',
        'construal__role__current_revision__metadatarevision',
        'construal__function__current_revision__metadatarevision') if these fields are not already being queried"""
        return mark_safe(f'<a href="{self.url}" class="{"misc-label" if self.special and self.special.strip() else "construal"}">{self.name_html}</a>')

    @cached_property
    def name_html(self):
        """For efficiency, callers should invoke .select_related(
        'construal__role__current_revision__metadatarevision',
        'construal__function__current_revision__metadatarevision') if these fields are not already being queried"""
        return self.special.strip() or format_html('{}&#x219d;{}', self.role.name_html, self.function.name_html)

    @cached_property
    def template(self):
        return "construal_article_view.html"

    class Meta:
        verbose_name = _('construal')
        unique_together = ('role', 'function', 'special')
        # issue #10: alphabetize models
        ordering = ['role', 'function', 'special']


class Case(MetaEnum):
    """Inventory of cases based on UniMorph <http://unimorph.org/>"""
    Unknown = UNK = 1

    # Core cases
    # Nominative-Accusative alignment
    Nominative = NOM = 2 ** 1
    Accusative = ACC = 2 ** 2
    # Ergative-Absolutive alignment
    Ergative = ERG = 2 ** 3
    Absolutive = ABS = 2 ** 4
    # Tripartite alignment
    NominativeSOnly = NOMS = 2 ** 5

    # Non-core, non-local cases
    Dative = DAT = 2 ** 6
    Benefactive = BEN = 2 ** 7
    Purposive = PRP = 2 ** 8
    Genitive = GEN = 2 ** 9
    Relative = REL = 2 ** 10
    Partitive = PRT = 2 ** 11
    Instrumental = INS = 2 ** 12
    Comitative = COM = 2 ** 13
    Vocative = VOC = 2 ** 14
    Comparative = COMPV = 2 ** 15
    Equative = EQTV = 2 ** 16
    Privative = PRIV = 2 ** 17
    Proprietive = PROPR = 2 ** 18
    Aversive = AVR = 2 ** 19
    Formal = FRML = 2 ** 20
    Translative = TRANS = 2 ** 21
    EssiveModal = BYWAY = 2 ** 22

    # Local cases
    # excluding Place cases
    # Distal
    Distal = REM = 2 ** 23
    Proximate = PROX = 2 ** 24
    # Motion
    Essive = ESS = 2 ** 25
    Allative = ALL = 2 ** 26
    Ablative = ABL = 2 ** 27
    # Aspect
    Approximative = APPRX = 2 ** 28
    Terminative = TERM = 2 ** 29

    @classmethod
    def longname(cls, val):
        return val.name

    @classmethod
    def shortname(cls, val):
        val = cls(val)
        return [k for k, v in cls.__members__.items() if v is val and k.isupper()][0]


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

    category = models.ForeignKey(ArticleCategory, null=False, related_name='language', on_delete=models.CASCADE)

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

    pre = models.PositiveIntegerField(choices=Presence.choices(),
                                      verbose_name="Prepositions/case prefixes or proclitics?")
    post = models.PositiveIntegerField(choices=Presence.choices(),
                                       verbose_name="Postpositions/case suffixes or enclitics?")
    circum = models.PositiveIntegerField(choices=Presence.choices(), verbose_name="Circumpositions/case circumfixes?")
    separate_word = models.PositiveIntegerField(choices=Presence.choices(),
                                                verbose_name="Adpositions/overt case markers can be separate words?")
    clitic_or_affix = models.PositiveIntegerField(choices=Presence.choices(),
                                                  verbose_name="Adpositions/overt case markers can be clitics or affixes?")

    # Maybe also: Does adposition/case morpheme ever encode other features,
    # like definiteness? Is there differential case marking?
    # Do all adpositions assign the same case? Which kinds of adpositions inflect e.g. for pronouns?

    # exclude_supersenses = models.ManyToManyField(Supersense, related_name="not_in_language", blank=True)

    class CaseSystemType(MetaEnum):
        none = 1
        pronominal = 2
        nominal = 3

    case_for = models.PositiveIntegerField(choices=CaseSystemType.choices(),
                                           verbose_name="Does the language have (affixal) case on nouns and pronouns, just pronouns, or neither?")
    cases = BitField(flags=Case.flags(), verbose_name="All cases present in the language")
    pobj_cases = BitField(flags=Case.flags(), verbose_name="All cases that ever apply to an adpositional object")

    @classmethod
    def with_nav_links(cls):
        return cls.objects.select_related('article__current_revision').filter(navlink=True, article__current_revision__deleted=False)

    def __str__(self):
        return self.name

    def morph_types(self):
        options = []
        default = None
        NONE = self.Presence.none

        if self.separate_word != NONE:
            if self.pre != NONE: options.append(Adposition.MorphType.from_properties('separate_word', 'pre'))
            if self.post != NONE: options.append(Adposition.MorphType.from_properties('separate_word', 'post'))
            if self.circum != NONE: options.append(Adposition.MorphType.from_properties('separate_word', 'circum'))
        if self.clitic_or_affix != NONE:
            if self.pre != NONE: options.append(Adposition.MorphType.from_properties('clitic_or_affix', 'pre'))
            if self.post != NONE: options.append(Adposition.MorphType.from_properties('clitic_or_affix', 'post'))
            if self.circum != NONE: options.append(Adposition.MorphType.from_properties('clitic_or_affix', 'circum'))

        if self.separate_word > self.clitic_or_affix:
            default_attachment = 'separate_word'
        elif self.separate_word < self.clitic_or_affix:
            default_attachment = 'clitic_or_affix'
        else:
            default_attachment = None

        default_position = max({'pre': self.pre, 'post': self.post, 'circum': self.circum}.items(), key=lambda x: x[1])
        if sum(1 for x in {self.pre, self.post, self.circum} if x == default_position[1]) > 1:
            default_position = None  # e.g., two "some" values but no "primary or sole" value
        else:
            default_position = default_position[0]

        if default_attachment and default_position:
            default = Adposition.MorphType.from_properties(default_attachment, default_position)

        return options, default

    @cached_property
    def template(self):
        return "language_article_view.html"

    @classmethod
    def editurl(cls, urlpath):
        # return "_plugin/metadata/editlang"
        return reverse('wiki:metadata_edit_language', args=[urlpath])

    class Meta:
        verbose_name = _('language')


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
            props2type = {('separate_word', 'pre'): cls.standalone_preposition,
                          ('separate_word', 'post'): cls.standalone_postposition,
                          ('separate_word', 'circum'): cls.standalone_circumposition,
                          ('clitic_or_affix', 'pre'): cls.prefix,
                          ('clitic_or_affix', 'post'): cls.suffix,
                          ('clitic_or_affix', 'circum'): cls.circumfix}
            if attachment is None or position is None:
                return props2type
            return props2type[attachment, position]

    class Transitivity(MetaEnum):
        always_intransitive = 0
        sometimes_transitive = 1
        always_transitive = 2

    # issue #51, add standard aposition spelling variants here
    def normalize_adp(cls, adp='', language_name=''):
        try:
            a_list = Adposition.objects.filter(current_revision__metadatarevision__adpositionrevision__name=adp)
            if not a_list:
                raise ObjectDoesNotExist()
            for a in a_list:
                a = a.current_revision.metadatarevision.adpositionrevision
                if a.lang.name == language_name or a.lang.slug == language_name:
                    return adp
            raise ObjectDoesNotExist()
        except ObjectDoesNotExist:
            for a in AdpositionRevision.objects.all():
                if not (a.lang.name==language_name or a.lang.slug==language_name):
                    continue
                if not a.other_forms:
                    continue
                if adp in a.other_forms:
                    return a.name
        return None

    def field_names(self):
        # issue #4: transliteration field
        return {'name', 'transliteration', 'other_forms', 'description', 'lang', 'morphtype', 'transitivity',
                'obj_cases', 'is_pp_idiom'}

    def __str__(self):
        if self.current_revision:
            return self.current_revision.metadatarevision.name
        else:
            return ugettext('Current revision not set!!')

    @cached_property
    def url(self):
        """For efficiency, callers should invoke .select_related('article')
        if this field is not already being queried"""
        return self.article.get_absolute_url()

    @cached_property
    def html(self):
        """For efficiency, callers should invoke .select_related('article',
        'current_revision__metadatarevision') if these fields are not already being queried"""
        return mark_safe(f'<a href="{self.url}" class="adposition">{self.name_html}</a>')

    @cached_property
    def name_html(self):    # technically this can change if a user edits the adposition name, but it's going to be rare
        """For efficiency, callers should invoke .select_related('current_revision__metadatarevision')
        if this field is not already being queried"""
        return format_html('{}', self.current_revision.metadatarevision.name)

    @cached_property
    def template(self):
        return "adposition_article_view.html"

    class Meta:
        verbose_name = _('adposition')

def adp_name_validator(value):
    if not value:
        raise ValidationError('Adposition name must not be null', code='invalid')
    x = re.search('[0-9]', value)
    if x:
        raise ValidationError(f'Adposition name must not contain a number: {x.group()} in {value}', code='invalid')


class AdpositionRevision(MetadataRevision):
    lang = models.ForeignKey(Language, related_name='adpositionrevisions', verbose_name='Language/dialect', on_delete=models.CASCADE)
    # name = models.CharField(max_length=200, verbose_name='Lemma',validators=[adp_name_validator] ,
    #     help_text="Lowercase unless it would normally be capitalized in a dictionary")
    # issue #4: transliteration field
    transliteration = models.CharField(max_length=200, blank=True, verbose_name="Transliteration",
                                       help_text="Romanization/phonemic spelling")
    other_forms = StringListField(max_length=200, blank=True, null=True, verbose_name="Other spellings or inflections",
                                   help_text="Exclude typos, Separate by spaces")
    morphtype = models.PositiveIntegerField(choices=Adposition.MorphType.choices(), verbose_name="Morphological type")
    transitivity = models.PositiveIntegerField(choices=Adposition.Transitivity.choices())
    obj_cases = BitField(flags=Case.flags(), verbose_name="Possible cases of the object")
    is_pp_idiom = models.BooleanField(default=False, verbose_name="Is PP Idiom?")

    unique_together = [('name', 'lang', 'revision_number')]

    def __str__(self):
        return ('Adposition Revision: %s %d') % (self.name, self.revision_number)

    @cached_property
    def url(self):
        """For efficiency, callers should invoke .select_related('article_revision__article')
        if this field is not already being queried"""
        return self.article_revision.article.get_absolute_url()

    @cached_property
    def html(self):
        """For efficiency, callers should invoke .select_related('article_revision__article')
        if this field is not already being queried"""
        return mark_safe(f'<a href="{self.url}" class="adposition">{self.name_html}</a>')

    @cached_property
    def name_html(self):    # technically this can change if a user edits the adposition name, but it's going to be rare
        return format_html('{}', self.name)


    @classmethod
    def editurl(cls, urlpath):
        # return "_plugin/metadata/editp"
        return reverse('wiki:metadata_edit_adposition', args=[urlpath])

    @cached_property
    def adposition(self): # TODO: another option: self.plugin.metadata.adposition
        return Adposition.objects.get(current_revision=self)

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

    @cached_property
    def url(self):
        """For efficiency, callers should invoke .select_related('article__current_revision')"""
        return self.article.get_absolute_url()

    @cached_property
    def html(self):
        return self.current_revision.metadatarevision.usagerevision.html

    @cached_property
    def template(self):
        return "usage_article_view.html"

    class Meta:
        verbose_name = _('usage')


class UsageRevision(MetadataRevision):
    adposition = models.ForeignKey(Adposition, null=True, related_name='usages', on_delete=models.CASCADE)
    obj_case = models.PositiveIntegerField(choices=Case.choices(), null=True)
    construal = models.ForeignKey(Construal, null=True, related_name='usages', on_delete=models.CASCADE)

    unique_together = [('adposition', 'obj_case', 'construal', 'revision_number')]

    def __str__(self):
        return ('Usage Revision: %s %d') % (self.name, self.revision_number)

    @cached_property
    def url(self):
        """For efficiency, callers should invoke .select_related('article_revision__article__current_revision')"""
        return self.article_revision.article.get_absolute_url()

    @cached_property
    def html(self):
        """For efficiency, callers should invoke .select_related('article_revision__article__current_revision',
        'adposition__current_revision__metadatarevision',
        'construal__role__current_revision__metadatarevision',
        'construal__function__current_revision__metadatarevision') if these fields are not already being queried"""
        special = self.construal.special and self.construal.special.strip()
        return mark_safe(f'<a href="{self.url}" class="usage">'
            f'<span class="adposition">{self.adposition.name_html}</span>: '
            f'<span class="{"misc-label" if special else "construal"}">{self.construal.name_html}</span></a>')

    class Meta:
        verbose_name = _('usage revision')
        # issue #10: alphabetize models
        ordering = ['adposition', 'construal']


# PTokenAnnotation fields:
# adp/adp lemma (foreign key), construal (foreign key), usage (foreign key),
# sentence (foreign key), case (optional), obj head, gov head,
# gov-obj syntactic configuration, POS of adp, POS of gov, POS of obj,
# Supersense of obj, Supersense of gov, list of subtokens (for mwe),
# list of weak associations (for mwe), is_gold, annotator note?,
# annotator grouping/cluster
#
# CorpusSentence fields:
# Corpus (foreign key), sent id, lang, orthography, is_parallel, doc id,
# offset within doc, sent text: original string, sent text: tokenized,
# word glosses?, sentence gloss?, note?
#
# Corpus fields
# Name, version, is_current, url, genre, lang(s), size?, stats?
def version_validator(value):
    if not value:
        raise ValidationError('Corpus version must not be null', code='invalid')
    x = re.search('[0-9]', value)
    if not x:
        raise ValidationError(f'Corpus version must contain a number', code='invalid')

class Corpus(SimpleMetadata):
    # Name, version, is_current, url, genre, lang(s), size?, stats?
    name = models.CharField(max_length=200, null=True, verbose_name="Corpus Name")
    version = models.CharField(max_length=200, null=True, validators=[version_validator], verbose_name="Version")
    url = models.URLField(max_length=200, blank=True, verbose_name="URL")
    genre = models.CharField(max_length=200, blank=True, verbose_name="Corpus Genre")
    description = models.CharField(max_length=200, blank=True, verbose_name="Description",
                                   help_text="Include number of tokens and basic statistics")
    languages = models.CharField(max_length=200, null=True, verbose_name="Language(s)")
    deprecated = models.BooleanField(default=False, verbose_name="Is this a deprecated version of a corpus?")

    def __str__(self):
        return self.name.lower() + self.version

    @classmethod
    def editurl(cls, urlpath):
        return reverse('wiki:metadata_edit_corpus', args=[urlpath])

    @cached_property
    def template(self):
        return "corpus_article_view.html"

    class Meta:
        verbose_name = _('corpus')
        verbose_name_plural = _('corpora')
        unique_together = [('name', 'version')]
        ordering = ['name', 'version']


class CorpusSentence(models.Model):
    # Corpus (foreign key), sent id, lang, orthography, is_parallel, doc id,
    # offset within doc, sent text: original string, sent text: tokenized,
    # word glosses?, sentence gloss?, note?
    corpus = models.ForeignKey(Corpus, null=True, related_name='corpus_sentences', on_delete=models.CASCADE)
    sent_id = models.CharField(max_length=200, null=True, verbose_name="Sentence ID")
    language = models.ForeignKey(Language, blank=True, related_name='corpus_sentences', on_delete=models.CASCADE)
    orthography = models.CharField(max_length=200, blank=True, verbose_name="Orthography",
                                   help_text="language-specific details such as style of transliteration")
    is_parallel = models.BooleanField(default=False)
    # parallel sentences
    # parallel = models.ManyToManyField(CorpusSentence, blank=True, related_name='parallel')
    doc_id = models.CharField(max_length=200, null=True, verbose_name="Document ID")
    text = models.CharField(max_length=1000, null=True, verbose_name="Text")
    tokens = StringListField(max_length=1000, null=True, verbose_name="Tokens")
    word_gloss = StringListField(max_length=200, blank=True, verbose_name="Word Gloss")
    sent_gloss = models.CharField(max_length=200, blank=True, verbose_name="Sentence Gloss")
    note = models.CharField(max_length=200, blank=True, verbose_name="Annotator Note")
    mwe_markup = models.CharField(max_length=200, blank=True, verbose_name="MWE Markup")

    @cached_property
    def url(self):
        return reverse('wiki:corpus_sentence_view', args=[self.language.slug, self.corpus, self.sent_id])

    @cached_property
    def html(self):
        return format_html(f'<a href="{self.url}" class="corpussentence">{{}}</a>', self.sent_id)

    @cached_property
    def template_name(self):
        return "corpus_sentence_view.html"

    def __str__(self):
        return str(self.corpus) + ': ' + self.sent_id

    class Meta:
        verbose_name = _('corpus sentence')
        unique_together = [('corpus', 'sent_id')]
        ordering = ['corpus', 'sent_id']

class ParallelSentenceAlignment(models.Model):

    source_sentence = models.ForeignKey(CorpusSentence,on_delete=models.CASCADE,related_name='source_sentence')
    target_sentence = models.ForeignKey(CorpusSentence,on_delete=models.CASCADE,related_name='target_sentence')

    @cached_property
    def html(self):
        return format_html(f'<a href="{self.url}" class="exnum">({{}})</a>', self.id)

    #def __str__(self):
    #    return str(self.adposition) + ' : ' + str(self.sentence)

    @cached_property
    def template_name(self):
        return "sentence_alignment_data_table.html"

    class Meta:
        verbose_name = _('parallel sentence alignment')
        unique_together = ('source_sentence', 'target_sentence')
        ordering = ['id']



class PTokenAnnotation(models.Model):
    # adp/adp lemma (foreign key), construal (foreign key), usage (foreign key),
    # sentence (foreign key), case (optional), obj head, gov head,
    # gov-obj syntactic configuration, POS of adp, POS of gov, POS of obj,
    # Supersense of obj, Supersense of gov, list of subtokens (for mwe),
    # list of weak associations (for mwe), is_gold, annotator note?,
    # annotator grouping/cluster
    token_indices = IntListField(max_length=200, blank=True, verbose_name="Token Indices")
    adposition = models.ForeignKey(Adposition, null=True, blank=True, on_delete=models.CASCADE)
    construal = models.ForeignKey(Construal, null=True, blank=True, related_name='ptoken_with_construal', on_delete=models.CASCADE)
    usage = models.ForeignKey(Usage, null=True, blank=True, on_delete=models.CASCADE)
    sentence = models.ForeignKey(CorpusSentence, null=True, on_delete=models.CASCADE)
    obj_case = models.PositiveIntegerField(choices=Case.choices(), blank=True)

    obj_head = models.CharField(max_length=200, null=True, verbose_name="Object Head")
    gov_head = models.CharField(max_length=200, null=True, verbose_name="Governor Head")
    gov_obj_syntax = models.CharField(max_length=200, null=True, verbose_name="Governor-Object Syntax")
    gov_head_index = models.PositiveIntegerField(null=True, verbose_name="Governor Index")
    obj_head_index  = models.PositiveIntegerField(null=True, verbose_name="Object Index")

    adp_pos = models.CharField(max_length=200, blank=True, verbose_name="Adposition Part of Speech")
    gov_pos = models.CharField(max_length=200, blank=True, verbose_name="Governor Part of Speech")
    obj_pos = models.CharField(max_length=200, blank=True, verbose_name="Object Part of Speech")

    gov_supersense = models.CharField(max_length=200, blank=True, verbose_name="Governor Supersense")
    obj_supersense = models.CharField(max_length=200, blank=True, verbose_name="Object Supersense")

    is_gold = models.BooleanField(default=False, verbose_name="Gold Annotation?")
    annotator_cluster = models.CharField(max_length=200, blank=True, verbose_name="Annotator Cluster",
                                         help_text='Informal Label for Grouping Similar Tokens')
    is_transitive = models.BooleanField(default=True, verbose_name="Transitive?",
                                        help_text='Does the adposition take an object?')
    is_typo  = models.BooleanField(default=False, verbose_name="Typo?")
    is_abbr  = models.BooleanField(default=False, verbose_name="Abbrev?")
    mwe_subtokens = StringListField(max_length=200, blank=True, verbose_name="MWE Subtokens")

    main_subtoken_indices = IntListField(max_length=200, blank=True, null=True, verbose_name="Main Subtoken Indices")
    main_subtoken_string = StringListField(max_length=200, blank=True, null=True, verbose_name="Main Subtoken String")

    @cached_property
    def exnum(self):
        """
        Example number to display in parentheses.
        Starts from 3000 to avoid clashing with examples defined in articles
        or looking like a year in a citation.
        """
        return self.id + 3000

    @cached_property
    def url(self):
        return reverse('wiki:ptoken_view', args=[self.exnum])

    @cached_property
    def html(self):
        """Linked example number in parentheses"""
        return format_html(f'<a href="{self.url}" class="exnum">({{}})</a>', self.exnum)

    def tokenhtml(self, offsets=False):
        """Linked main token(s) (the contiguous part of the expression): actual tokens, not lemmas.
        If offsets is True, specify token offsets as the title attribute of each word."""
        i, j = self.main_subtoken_indices[0]-1, self.main_subtoken_indices[-1]
        displaystr = ' '.join(format_html('<span title="{}">{}</span>', h, t) for h,t in enumerate(self.sentence.tokens[i:j], start=i+1))
        return mark_safe(f'<a href="{self.url}" class="exnum">' + displaystr + '</a>')

    @cached_property
    def template_name(self):
        return "ptoken_view.html"


    def __str__(self):
        return str(self.adposition) + ' : ' + str(self.sentence)

    class Meta:
        verbose_name = _('adposition token annotation')
        unique_together = ('sentence', 'token_indices')
        # issue #10: alphabetize models
        ordering = ['sentence', 'token_indices']


class ParallelPTokenAlignment(models.Model):

    source_example = models.ForeignKey(PTokenAnnotation,on_delete=models.CASCADE,related_name="source_example")
    target_example = models.ForeignKey(PTokenAnnotation, on_delete=models.CASCADE, related_name="target_example")

    @cached_property
    def template_name(self):
        return "ptoken_alignment_data_table.html"


    class Meta:
        verbose_name = _('adposition alignment')
        unique_together = ('source_example', 'target_example')
        ordering = ['id']


# You must register the model here

admin.site.register(Supersense)
# admin.site.register(SupersenseRevision)
# admin.site.register(Construal)
admin.site.register(Language)
admin.site.register(Adposition)
# admin.site.register(AdpositionRevision)
admin.site.register(Usage)
# admin.site.register(UsageRevision)
admin.site.register(Corpus)
