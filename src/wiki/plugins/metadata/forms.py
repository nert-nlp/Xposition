
from __future__ import absolute_import, unicode_literals
from wiki.models import URLPath
from django.utils.safestring import mark_safe
from django import forms
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.shortcuts import get_object_or_404, redirect, render
from django.core.validators import _lazy_re_compile, RegexValidator
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext
from wiki.core.plugins.base import PluginSidebarFormMixin
from . import models
from .models import deepest_instance
from wiki.plugins.categories.models import ArticleCategory
from wiki.models import ArticleRevision
import wiki.forms
from wiki.conf import settings
import copy, sys
import regex

'''
class HorizontalRadioSelect(forms.RadioSelect):
    """Adapted from https://stackoverflow.com/a/39538735"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        css_style = 'style="display: inline-block; margin-right: 10px;"'
        self.renderer.outer_html = '<ul{id_attr} style="display: inline-block">{content}</ul>'
        self.renderer.inner_html = '<li ' + css_style + '>{choice_value}{sub_widgets}</li>'
'''



class ArticleMetadataForm(forms.ModelForm):
    """
    Base class for building a form for a model with an associated article,
    and optionally, an associated ArticleCategory.
    The form allows creation of a new model instance with its associated article/category,
    or for editing an existing model instance. (Attaching a new model instance
    to an existing article/category is not supported.)
    Once created, the associated article/category can be edited elsewhere.
    The model instance cannot be detached from the article/category.

    Subclasses are recommended to supply new() and edit() methods
    that will be called by save() as appropriate.
    """
    def __init__(self, article, request, *args, disable_on_edit=('name','slug'), **kwargs):
        self.article = article #kwargs['article']  # the article in the URL path
        self.request = request #kwargs['request']
        super(ArticleMetadataForm, self).__init__(*args, **kwargs)
        if self.instance.id and disable_on_edit:    # editing an existing instance
            for fldname in disable_on_edit:
                self.fields[fldname].disabled = True

    def newArticle(self, name=None, slug=None, parent=None):
        self.article_urlpath = URLPath.create_article(
            parent=parent or URLPath.root(),
            slug=slug or self.data['slug'],
            title=name or self.data['name'],
            content=name or self.data['name'],
            user_message=" ",
            user=self.request.user,
            article_kwargs={'owner': self.request.user,
                            'group': self.article.group,
                            'group_read': self.article.group_read,
                            'group_write': self.article.group_write,
                            'other_read': self.article.other_read,
                            'other_write': self.article.other_write,
                            })
        newarticle = models.Article.objects.get(urlpath = self.article_urlpath)
        return newarticle

    def newArticle_ArticleCategory(self, name=None, parent=None, slug=None):
        newarticle = self.newArticle(name=name or self.cleaned_data['name'],
                                     slug=slug or name or self.cleaned_data['slug'],
                                     parent=parent)
        newcategory = ArticleCategory(slug=name or self.cleaned_data['slug'],
                                      name=name or self.cleaned_data['name'],
                                      description=self.cleaned_data.get('description', name or self.cleaned_data['name']),
                                      parent=self.cleaned_data['parent'].category if self.cleaned_data.get('parent') else None)
        newcategory.article = newarticle
        newcategory.save()
        return newarticle, newcategory

    def newArticle_without_category(self, name=None, parent=None, slug=None):
        newarticle = self.newArticle(name=name or self.cleaned_data['name'],
                                     slug=slug or name or self.cleaned_data['slug'],
                                     parent=parent)
        newarticle.save()
        return newarticle

    def save(self, commit=True):
        m = super(ArticleMetadataForm, self).save(commit=False)
        if self.instance.id:
            return self.edit(m, commit=commit)
        return self.new(m, commit=commit)

    @property
    def auto_slug(self):
        """If there is a slug field, should it be autofilled when typing in the name field?"""
        return True

# From http://forums.mozillazine.org/viewtopic.php?f=25&t=834075
"""
UNICODE_LETTERS_MARKS_HYPHEN_APPOS is [-_\'], all Unicode Letters, Nonspacing Marks, and Spacing Marks
"""

UNICODE_LETTERS_MARKS_HYPHEN_APPOS = r'^[-_\'\p{L}\p{Mn}\p{Mc}]+$'

slug_mod_unicode_re = regex.compile(r'^[-_\'\p{Letter}\p{Mn}\p{Mc}]+\Z')
validate_unicode_slug_mod = RegexValidator(
    slug_mod_unicode_re,
    _("Enter a valid 'slug' consisting of Unicode letters, numbers, underscores, hyphens, or apostrophes. Rule of thumb: spell the word as it would appear in a Wiktionary URL (which for some languages means omitting certain diacritics)."),
    'invalid'
)
validate_slug_numbers = RegexValidator(
    r'^\d+$',
    _("A 'slug' cannot consist solely of numbers."),
    'invalid',
    inverse_match=True
)
class ModSlugField(forms.SlugField):
    default_validators = [validate_unicode_slug_mod, validate_slug_numbers]

class SupersenseForm(ArticleMetadataForm):

    slug = ModSlugField(max_length=200)

    def __init__(self, article, request, *args, **kwargs):
        super(SupersenseForm, self).__init__(article, request, *args, **kwargs)

        # use horizontal radio buttons (requires metadata.css)
        self.fields['animacy'].widget.attrs={'class': 'inline'}

        # set up the slug text field, modeled after the create article page
        self.fields['slug'].widget = wiki.forms.TextInputPrepend(
            prepend='/', # + self.urlpath.path,
            attrs={
                'pattern': '^[A-Z][-A-Za-z]*[a-z][-A-Za-z]*$',
                'title': 'Initial capital letter plus ASCII letters (at least one lowercase) and hyphens'
            }
        )

    def edit(self, m, commit=True):
        thesupersense = self.instance.supersense
        if self.cleaned_data['parent']:
            thesupersense.category.parent = self.cleaned_data['parent'].category
        else:
            thesupersense.category.parent = None
        thesupersense.newRevision(self.request, commit=commit, **self.cleaned_data)
        # no change to the present model instance (the previous SupersenseRevision)
        if commit:
            thesupersense.category.save()
        return thesupersense.article.urlpath_set.all()[0]

    def new(self, m, commit=True):
        newarticle, newcategory = self.newArticle_ArticleCategory()
        # associate the article with the SupersenseRevision
        m.article = newarticle

        # create the Supersense, add the article, category, and revision
        supersense = models.Supersense()
        supersense.article = newarticle
        supersense.category = newcategory
        if self.cleaned_data['parent']:
            supersense.category.parent = self.cleaned_data['parent'].category   # the parent category is stored both on the revision and on the Supersense.category
        else:
            supersense.category.parent = None
        supersense.add_revision(m, self.request, article_revision=newarticle.current_revision, save=True) # cannot delay saving the new supersense revision

        if commit:
            m.save()
            supersense.save()
        return self.article_urlpath

    class Meta:
        model = models.SupersenseRevision
        fields = ('name', 'description', 'parent', 'animacy', 'deprecated', 'deprecation_message')
        labels = {'description': _('Short Description')}
        widgets = {'animacy': forms.RadioSelect}


def morphtype_validator(lang, forbidden_vals):
    """forbidden_vals is a sequence of MorphType constants that are
    incompatible with this field being set to NONE if they appear
    for any of the language's adpositions"""
    NONE = models.Language.Presence.none
    Adp = models.Adposition
    def validator(value):
        if int(value)!=NONE: return
        Ps = []
        for forbidden in forbidden_vals:
            Ps += list(Adp.objects.filter(current_revision__metadatarevision__adpositionrevision__lang=lang,
                                          current_revision__metadatarevision__adpositionrevision__morphtype=forbidden))
        if Ps:
            raise ValidationError(f'This language has {len(Ps)} adposition(s) of this type, including "{Ps[0]}"', code='invalid')
    return validator

class LanguageForm(ArticleMetadataForm):

    def __init__(self, article, request, *args, **kwargs):
        super(LanguageForm, self).__init__(article, request, *args, **kwargs)

        # set up the slug text field, modeled after the create article page
        self.fields['slug'].widget = wiki.forms.TextInputPrepend(
            prepend='/', # + self.urlpath.path,
            attrs={
                'pattern': '^[a-z][-a-z]+$',
                'title': 'Lowercase letters and hyphens'
            }
        )
        if self.instance.id:
            MT = models.Adposition.MorphType
            self.fields['pre'].validators.append(morphtype_validator(self.instance,
                (MT.prefix, MT.standalone_preposition)))
            self.fields['post'].validators.append(morphtype_validator(self.instance,
                (MT.suffix, MT.standalone_postposition)))
            self.fields['circum'].validators.append(morphtype_validator(self.instance,
                (MT.circumfix, MT.standalone_circumposition)))
            self.fields['separate_word'].validators.append(morphtype_validator(self.instance,
                (MT.standalone_preposition, MT.standalone_postposition, MT.standalone_circumposition)))
            self.fields['clitic_or_affix'].validators.append(morphtype_validator(self.instance,
                (MT.prefix, MT.suffix, MT.circumfix)))

        # use horizontal radio buttons/checkboxes (requires metadata.css)
        for f in self.fields.values():
            if isinstance(f.widget, (forms.RadioSelect,forms.CheckboxSelectMultiple)):
                f.widget.attrs={'class': 'inline'}
            if isinstance(f.widget, forms.RadioSelect):
                if f.widget.choices[0][0]=='':
                    f.widget.choices = f.widget.choices[1:] # remove the empty default

    def edit(self, m, commit=True):
        if commit:
            m.save()
        return m.article.urlpath_set.all()[0]

    def new(self, m, commit=True):
        newarticle, newcategory = self.newArticle_ArticleCategory()
        m.article = newarticle
        m.category = newcategory
        if commit:
            m.save()
        return self.article_urlpath

    @property
    def auto_slug(self):
        return False

    class Meta:
        model = models.Language
        exclude = ('article', 'deleted', 'current_revision', 'category')
        widgets = {f: forms.RadioSelect for f in {'pre','post','circum','separate_word','clitic_or_affix','case_for'}}


class AdpositionForm(ArticleMetadataForm):

    slug = ModSlugField(max_length=200)

    def __init__(self, article, request, *args, **kwargs):
        """If no initial data, provide some defaults."""
        initial = kwargs.get('initial', {})
        if 'obj_cases' not in initial:
            # initialize all cases as checked (the choices will be filtered later based on the language)
            initial['obj_cases'] = [case for case in models.AdpositionRevision.obj_cases]
        kwargs['initial'] = initial

        super(AdpositionForm, self).__init__(article, request, disable_on_edit=('name','slug','lang'), *args, **kwargs)

        try:
            lang = models.Language.objects.get(article=article)
        except models.Language.DoesNotExist:
            lang = article.current_revision.metadata_revision.adpositionrevision.lang
            self.article = lang.article # so we don't put the new article under another adposition article
        self.fields['lang'].initial = lang
        self.fields['lang'].choices = [(lang.id, lang.name)]

        # set up the slug text field, modeled after the create article page
        self.fields['slug'].widget = wiki.forms.TextInputPrepend(
            prepend='/' + self.article.urlpath_set.all()[0].path,
            attrs={
                'pattern': UNICODE_LETTERS_MARKS_HYPHEN_APPOS,
                'title': 'Letters, hyphens, underscores, apostrophes'
            }
        )

        morphtype_options, morphtype_default = lang.morph_types()
        morphtype_choices = [(o.value, o.name.replace('_',' ')) for o in morphtype_options]
        self.fields['morphtype'].choices = morphtype_choices
        #assert False
        if morphtype_default:
            self.fields['morphtype'].initial = int(morphtype_default)

        # limit case options to those allowed by Language
        self.fields['obj_cases'].widget.choices = [(case, case) for case,allowed in lang.pobj_cases if allowed]
        # will be checked by default due to initialization above
        # this is good for English (Accusative is the only option, always checked)

        # use horizontal radio buttons/checkboxes (requires metadata.css)
        for f in self.fields.values():
            if isinstance(f.widget, (forms.RadioSelect,forms.CheckboxSelectMultiple)):
                f.widget.attrs={'class': 'inline'}
            if isinstance(f.widget, forms.RadioSelect):
                if f.widget.choices[0][0]=='':
                    f.widget.choices = f.widget.choices[1:] # remove the empty default

    def edit(self, m, commit=True):
        thep = self.instance.adposition
        thep.newRevision(self.request, commit=commit, **self.cleaned_data)
        # no change to the present model instance (the previous SupersenseRevision)
        return thep.article.urlpath_set.all()[0]

    def new(self, m, commit=True):
        newarticle = self.newArticle_without_category(parent=self.article.urlpath_set.all()[0])
        # associate the article with the SupersenseRevision
        m.article = newarticle

        # create the Supersense, add the article, category, and revision
        p = models.Adposition()
        p.article = newarticle
        p.add_revision(m, self.request, article_revision=newarticle.current_revision, save=True) # cannot delay saving the new adposition revision

        if commit:
            m.save()
            p.save()
        return self.article_urlpath

    class Meta:
        model = models.AdpositionRevision
		# issue #4: transliteration field
        fields = ('lang', 'name', 'transliteration', 'other_forms', 'description', 'morphtype', 'transitivity', 'slug', 'obj_cases', 'is_pp_idiom')
        widgets = {f: forms.RadioSelect for f in {'morphtype', 'transitivity'}}


class ConstrualForm(ArticleMetadataForm):

    def __init__(self, article, request, *args, **kwargs):
        super(ConstrualForm, self).__init__(article, request, *args, **kwargs)
        self.fields['role'].queryset = models.Supersense.objects.filter(current_revision__metadatarevision__supersenserevision__deprecated=False)
        self.fields['function'].queryset = models.Supersense.objects.filter(current_revision__metadatarevision__supersenserevision__deprecated=False)

    def edit(self, m, commit=True):
        if commit:
            m.save()
        return m.article.urlpath_set.all()[0]

    def new(self, m, commit=True):
        role_name = deepest_instance(self.cleaned_data['role'].current_revision).name
        function_name = deepest_instance(self.cleaned_data['function'].current_revision).name
        name = self.get_construal_slug(role_name, function_name)
        # slug will be the same as name
        newarticle = self.newArticle_without_category(name=name)
        m.article = newarticle
        if commit:
            m.save()
        return self.article_urlpath

    @classmethod
    def get_construal_slug(cls, role_name, function_name):
        return role_name + '--' + function_name

    class Meta:
        model = models.Construal
        fields = ('role', 'function')


class UsageForm(ArticleMetadataForm):

    def __init__(self, article, request, *args, **kwargs):
        # """If no initial data, provide some defaults."""
        # initial = kwargs.get('initial', {})
        # if 'obj_case' not in initial:
        #     # initialize all cases as checked (the choices will be filtered later based on the language)
        #     initial['obj_case'] = [case for case in models.AdpositionRevision.obj_cases]
        # kwargs['initial'] = initial

        super(UsageForm, self).__init__(article, request, *args, **kwargs)

        try:
            adp = models.Adposition.objects.get(article=article)
        except models.Adposition.DoesNotExist:
            adp = article.current_revision.metadata_revision.usagerevision.adposition
            self.article = adp.article # so we don't put the new article under another usage article
        self.fields['adposition'].initial = adp
        self.fields['adposition'].choices = [(adp.id, str(adp))]
        self.fields['obj_case'].choices = [(int(models.Case[case]),case) for case,allowed in deepest_instance(adp.current_revision).obj_cases if allowed]
        if len(self.fields['obj_case'].choices)==1:
            self.fields['obj_case'].initial = self.fields['obj_case'].choices[0][0]
            self.fields['obj_case'].required = True
        elif len(self.fields['obj_case'].choices)==0:
            self.fields['obj_case'].required = False
        else:
            self.fields['obj_case'].required = True

        # use horizontal radio buttons (requires metadata.css)
        for fname,f in self.fields.items():
            if isinstance(f.widget, forms.RadioSelect):
                f.widget.attrs={'class': 'inline'}

    def edit(self, m, commit=True):
        assert False,"Editing a Usage is not currently supported."

    def new(self, m, commit=True):
        if len(self.fields['obj_case'].choices)<2:
            case = None
        else:
            case = models.Case.shortname(self.cleaned_data['obj_case'])
        caseSlug = '<'+case+'>' if case else ''
        construalSlug = m.construal.article.urlpath_set.all()[0].slug
        name = self.get_usage_name(deepest_instance(m.adposition.current_revision).name,
                                   str(m.construal),
                                   case)
        newarticle = self.newArticle_without_category(parent=self.article.urlpath_set.all()[0],
                                                                   name=name,
                                                                   slug=caseSlug + construalSlug)
        # associate the article with the SupersenseRevision
        m.article = newarticle
        m.name = name
        # TODO: maybe set the description

        # create the Supersense, add the article, category, and revision
        u = models.Usage()
        u.article = newarticle
        u.add_revision(m, self.request, article_revision=newarticle.current_revision, save=True) # cannot delay saving the new adposition revision

        if commit:
            m.save()
            u.save()
        return self.article_urlpath

    @classmethod
    def get_usage_name(cls, adp_name, construal_name, case=None):
        """Provide 'case' only if it is potentially ambiguous for this adposition"""
        casespec = '<'+case+'>' if case else ''
        return adp_name + casespec + ': ' + construal_name

    class Meta:
        model = models.UsageRevision
        fields = ('adposition', 'obj_case', 'construal')
        widgets = {'obj_case': forms.RadioSelect}

class CorpusForm(ArticleMetadataForm):

    def __init__(self, article, request, *args, **kwargs):
        super(CorpusForm, self).__init__(article, request, *args, **kwargs)

    def edit(self, m, commit=True):
        if commit:
            m.save()
        return m.article.urlpath_set.all()[0]

    def new(self, m, commit=True):
        name = m.name
        version = m.version
        slug = self.get_corpus_slug(name, version)
        newarticle = self.newArticle_without_category(name=name,
                                                                   parent=self.article.urlpath_set.all()[0],
                                                                   slug=slug)
        m.article = newarticle
        if commit:
            m.save()
        return self.article_urlpath


    def get_corpus_slug(self, name, version):
        return ''+str(name).lower()+str(version)

    class Meta:
        model = models.Corpus

        fields = ('name', 'version', 'url', 'genre', 'description', 'languages')




def MetaSidebarForm(article, request, *args, **kwargs):
    """
    Each plugin sets a form_class attribute for use when instantiating a sidebar form.
    Setting form_class=MetaSidebarForm allows for dynamic selection of the class
    depending on the type of metadata attached to the article. The classes need
    to be declared separately in order for ModelForm metaclasses to work.
    """
    try:
        metadata = models.SimpleMetadata.objects.get(article = article)
    except models.SimpleMetadata.DoesNotExist:
        try:
            metadata = models.Metadata.objects.get(article = article)
        except models.Metadata.DoesNotExist:
            return EmptySidebarForm()

    metad = deepest_instance(metadata)
    themodel = type(metad)

    return EmptySidebarForm()

    # TODO: dead code
    if themodel is models.Supersense:
        metac = deepest_instance(metad.current_revision)
        kwargs['instance'] = metac
        x = SupersenseSidebarForm(article, request, metad, *args, **kwargs)
    elif themodel is models.Language:
        kwargs['instance'] = metad
        x = LanguageSidebarForm(article, request, metad, *args, **kwargs)
    return x

class EmptySidebarForm():
    pass

class BaseMetaSidebarForm(PluginSidebarFormMixin):
    def __init__(self, article, request, metad, *args, **kwargs):
        self.article = article
        self.request = request
        self.metadata = metad #models.Metadata.objects.get(article = self.article)


        super(BaseMetaSidebarForm, self).__init__(*args, **kwargs)


class SupersenseSidebarForm(BaseMetaSidebarForm):
    class Meta:
        model = models.SupersenseRevision
        fields = ('animacy', 'description')
        labels = {'description': _('Short Description')}

    def save(self, *args, **kwargs):
        if self.is_valid():
            self.metacurr.newRevision(self.request, **self.cleaned_data)

class LanguageSidebarForm(BaseMetaSidebarForm):
    class Meta:
        model = models.Language
        exclude = ('article', 'deleted', 'current_revision', 'category')

class ExampleForm(forms.Form):

    def __init__(self, article, request, *args, **kwargs):
        self.article = article
        self.request = request
        super(ExampleForm, self).__init__(*args, **kwargs)

    example_Title = forms.CharField()
    example_File = forms.FileField()
