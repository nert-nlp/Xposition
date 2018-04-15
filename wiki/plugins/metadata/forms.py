
from __future__ import absolute_import, unicode_literals
from wiki.models import URLPath
from django.utils.safestring import mark_safe
from django import forms
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
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
UNICODE_LETTERS_NUMERICS_HYPHEN_APPOS = (
    r'^[-_\'\u0041-\u005A\u0061-\u007A\u00AA\u00B5\u00BA\u00C0-\u00D6\u00D8-\u00F6'
    r'\u00F8-\u02C1\u02C6-\u02D1\u02E0-\u02E4\u02EC\u02EE\u0370-\u0374'
    r'\u0376-\u0377\u037A-\u037D\u0386\u0388-\u038A\u038C\u038E-\u03A1'
    r'\u03A3-\u03F5\u03F7-\u0481\u048A-\u0523\u0531-\u0556\u0559\u0561-\u0587'
    r'\u05D0-\u05EA\u05F0-\u05F2\u0621-\u064A\u066E-\u066F\u0671-\u06D3\u06D5'
    r'\u06E5-\u06E6\u06EE-\u06EF\u06FA-\u06FC\u06FF\u0710\u0712-\u072F'
    r'\u074D-\u07A5\u07B1\u07CA-\u07EA\u07F4-\u07F5\u07FA\u0904-\u0939\u093D'
    r'\u0950\u0958-\u0961\u0971-\u0972\u097B-\u097F\u0985-\u098C\u098F-\u0990'
    r'\u0993-\u09A8\u09AA-\u09B0\u09B2\u09B6-\u09B9\u09BD\u09CE\u09DC-\u09DD'
    r'\u09DF-\u09E1\u09F0-\u09F1\u0A05-\u0A0A\u0A0F-\u0A10\u0A13-\u0A28'
    r'\u0A2A-\u0A30\u0A32-\u0A33\u0A35-\u0A36\u0A38-\u0A39\u0A59-\u0A5C\u0A5E'
    r'\u0A72-\u0A74\u0A85-\u0A8D\u0A8F-\u0A91\u0A93-\u0AA8\u0AAA-\u0AB0'
    r'\u0AB2-\u0AB3\u0AB5-\u0AB9\u0ABD\u0AD0\u0AE0-\u0AE1\u0B05-\u0B0C'
    r'\u0B0F-\u0B10\u0B13-\u0B28\u0B2A-\u0B30\u0B32-\u0B33\u0B35-\u0B39\u0B3D'
    r'\u0B5C-\u0B5D\u0B5F-\u0B61\u0B71\u0B83\u0B85-\u0B8A\u0B8E-\u0B90'
    r'\u0B92-\u0B95\u0B99-\u0B9A\u0B9C\u0B9E-\u0B9F\u0BA3-\u0BA4\u0BA8-\u0BAA'
    r'\u0BAE-\u0BB9\u0BD0\u0C05-\u0C0C\u0C0E-\u0C10\u0C12-\u0C28\u0C2A-\u0C33'
    r'\u0C35-\u0C39\u0C3D\u0C58-\u0C59\u0C60-\u0C61\u0C85-\u0C8C\u0C8E-\u0C90'
    r'\u0C92-\u0CA8\u0CAA-\u0CB3\u0CB5-\u0CB9\u0CBD\u0CDE\u0CE0-\u0CE1'
    r'\u0D05-\u0D0C\u0D0E-\u0D10\u0D12-\u0D28\u0D2A-\u0D39\u0D3D\u0D60-\u0D61'
    r'\u0D7A-\u0D7F\u0D85-\u0D96\u0D9A-\u0DB1\u0DB3-\u0DBB\u0DBD\u0DC0-\u0DC6'
    r'\u0E01-\u0E30\u0E32-\u0E33\u0E40-\u0E46\u0E81-\u0E82\u0E84\u0E87-\u0E88'
    r'\u0E8A\u0E8D\u0E94-\u0E97\u0E99-\u0E9F\u0EA1-\u0EA3\u0EA5\u0EA7'
    r'\u0EAA-\u0EAB\u0EAD-\u0EB0\u0EB2-\u0EB3\u0EBD\u0EC0-\u0EC4\u0EC6'
    r'\u0EDC-\u0EDD\u0F00\u0F40-\u0F47\u0F49-\u0F6C\u0F88-\u0F8B\u1000-\u102A'
    r'\u103F\u1050-\u1055\u105A-\u105D\u1061\u1065-\u1066\u106E-\u1070'
    r'\u1075-\u1081\u108E\u10A0-\u10C5\u10D0-\u10FA\u10FC\u1100-\u1159'
    r'\u115F-\u11A2\u11A8-\u11F9\u1200-\u1248\u124A-\u124D\u1250-\u1256\u1258'
    r'\u125A-\u125D\u1260-\u1288\u128A-\u128D\u1290-\u12B0\u12B2-\u12B5'
    r'\u12B8-\u12BE\u12C0\u12C2-\u12C5\u12C8-\u12D6\u12D8-\u1310\u1312-\u1315'
    r'\u1318-\u135A\u1380-\u138F\u13A0-\u13F4\u1401-\u166C\u166F-\u1676'
    r'\u1681-\u169A\u16A0-\u16EA\u16EE-\u16F0\u1700-\u170C\u170E-\u1711'
    r'\u1720-\u1731\u1740-\u1751\u1760-\u176C\u176E-\u1770\u1780-\u17B3\u17D7'
    r'\u17DC\u1820-\u1877\u1880-\u18A8\u18AA\u1900-\u191C\u1950-\u196D'
    r'\u1970-\u1974\u1980-\u19A9\u19C1-\u19C7\u1A00-\u1A16\u1B05-\u1B33'
    r'\u1B45-\u1B4B\u1B83-\u1BA0\u1BAE-\u1BAF\u1C00-\u1C23\u1C4D-\u1C4F'
    r'\u1C5A-\u1C7D\u1D00-\u1DBF\u1E00-\u1F15\u1F18-\u1F1D\u1F20-\u1F45'
    r'\u1F48-\u1F4D\u1F50-\u1F57\u1F59\u1F5B\u1F5D\u1F5F-\u1F7D\u1F80-\u1FB4'
    r'\u1FB6-\u1FBC\u1FBE\u1FC2-\u1FC4\u1FC6-\u1FCC\u1FD0-\u1FD3\u1FD6-\u1FDB'
    r'\u1FE0-\u1FEC\u1FF2-\u1FF4\u1FF6-\u1FFC\u2071\u207F\u2090-\u2094\u2102'
    r'\u2107\u210A-\u2113\u2115\u2119-\u211D\u2124\u2126\u2128\u212A-\u212D'
    r'\u212F-\u2139\u213C-\u213F\u2145-\u2149\u214E\u2160-\u2188\u2C00-\u2C2E'
    r'\u2C30-\u2C5E\u2C60-\u2C6F\u2C71-\u2C7D\u2C80-\u2CE4\u2D00-\u2D25'
    r'\u2D30-\u2D65\u2D6F\u2D80-\u2D96\u2DA0-\u2DA6\u2DA8-\u2DAE\u2DB0-\u2DB6'
    r'\u2DB8-\u2DBE\u2DC0-\u2DC6\u2DC8-\u2DCE\u2DD0-\u2DD6\u2DD8-\u2DDE\u2E2F'
    r'\u3005-\u3007\u3021-\u3029\u3031-\u3035\u3038-\u303C\u3041-\u3096'
    r'\u309D-\u309F\u30A1-\u30FA\u30FC-\u30FF\u3105-\u312D\u3131-\u318E'
    r'\u31A0-\u31B7\u31F0-\u31FF\u3400\u4DB5\u4E00\u9FC3\uA000-\uA48C'
    r'\uA500-\uA60C\uA610-\uA61F\uA62A-\uA62B\uA640-\uA65F\uA662-\uA66E'
    r'\uA67F-\uA697\uA717-\uA71F\uA722-\uA788\uA78B-\uA78C\uA7FB-\uA801'
    r'\uA803-\uA805\uA807-\uA80A\uA80C-\uA822\uA840-\uA873\uA882-\uA8B3'
    r'\uA90A-\uA925\uA930-\uA946\uAA00-\uAA28\uAA40-\uAA42\uAA44-\uAA4B\uAC00'
    r'\uD7A3\uF900-\uFA2D\uFA30-\uFA6A\uFA70-\uFAD9\uFB00-\uFB06\uFB13-\uFB17'
    r'\uFB1D\uFB1F-\uFB28\uFB2A-\uFB36\uFB38-\uFB3C\uFB3E\uFB40-\uFB41'
    r'\uFB43-\uFB44\uFB46-\uFBB1\uFBD3-\uFD3D\uFD50-\uFD8F\uFD92-\uFDC7'
    r'\uFDF0-\uFDFB\uFE70-\uFE74\uFE76-\uFEFC\uFF21-\uFF3A\uFF41-\uFF5A'
    r'\uFF66-\uFFBE\uFFC2-\uFFC7\uFFCA-\uFFCF\uFFD2-\uFFD7\uFFDA-\uFFDC]+$'
    )

slug_mod_unicode_re = _lazy_re_compile(r'^[-\'\w]+\Z')
validate_unicode_slug_mod = RegexValidator(
    slug_mod_unicode_re,
    _("Enter a valid 'slug' consisting of Unicode letters, numbers, underscores, hyphens, or apostrophes."),
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
        fields = ('name', 'description', 'parent', 'animacy')
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

        # issue #23: disallow language with no adposition or affix type
        ps = [m.pre, m.post, m.circum]
        ms = [m.separate_word, m.clitic_or_affix]
        No = models.Language.Presence.none
        if all([p==No for p in ps]) or all([p==No for p in ms]):
            raise forms.ValidationError(ugettext('You need to choose at least one type of adposition or affix!'))

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
                'pattern': UNICODE_LETTERS_NUMERICS_HYPHEN_APPOS,
                'title': 'Letters, numbers, hyphens, underscores, apostrophes'
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
        newarticle, newcategory = self.newArticle_ArticleCategory(parent=self.article.urlpath_set.all()[0])
        # associate the article with the SupersenseRevision
        m.article = newarticle

        # create the Supersense, add the article, category, and revision
        p = models.Adposition()
        p.article = newarticle
        p.category = newcategory
        p.add_revision(m, self.request, article_revision=newarticle.current_revision, save=True) # cannot delay saving the new adposition revision

        if commit:
            m.save()
            p.save()
        return self.article_urlpath

    class Meta:
        model = models.AdpositionRevision
		# issue #4: transliteration field
        fields = ('lang', 'name', 'transliteration', 'other_forms', 'description', 'morphtype', 'transitivity', 'slug', 'obj_cases')
        widgets = {f: forms.RadioSelect for f in {'morphtype', 'transitivity'}}


class ConstrualForm(ArticleMetadataForm):

    def __init__(self, article, request, *args, **kwargs):
        super(ConstrualForm, self).__init__(article, request, *args, **kwargs)

    def edit(self, m, commit=True):
        if commit:
            m.save()
        return m.article.urlpath_set.all()[0]

    def new(self, m, commit=True):
        role_name = deepest_instance(self.cleaned_data['role'].current_revision).name
        function_name = deepest_instance(self.cleaned_data['function'].current_revision).name
        name = self.get_construal_slug(role_name, function_name)
        # slug will be the same as name
        newarticle, newcategory = self.newArticle_ArticleCategory(name=name)
        m.article = newarticle
        m.category = newcategory
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
        newarticle, newcategory = self.newArticle_ArticleCategory(parent=self.article.urlpath_set.all()[0],
                                                                  name=name,
                                                                  slug=caseSlug + construalSlug)
        # associate the article with the SupersenseRevision
        m.article = newarticle
        m.name = name
        # TODO: maybe set the description

        # create the Supersense, add the article, category, and revision
        u = models.Usage()
        u.article = newarticle
        u.category = newcategory
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
