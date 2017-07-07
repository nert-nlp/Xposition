
from __future__ import absolute_import, unicode_literals

from django.utils.safestring import mark_safe
from django import forms
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext
from wiki.core.plugins.base import PluginSidebarFormMixin
from wiki import models

# It would be cleaner if we combined the SidebarForm and EditCategoryForm, however the logic of
# the form might be too complex if we do

class CategoryForm(forms.ModelForm):

    '''Simple model form for category creation, edit this to hide fields that are unnecessary'''
    def __init__(self, *args, **kwargs):
        super(CategoryForm, self).__init__(*args, **kwargs)

    def save(self, *args, **kwargs):
        super(CategoryForm, self).save(*args, **kwargs)

    class Meta:
        model = models.Category
        fields = ('__all__')


class SidebarForm(PluginSidebarFormMixin):

    ''' This edit form allows us to change what categories an article is in '''
    def __init__(self, article, request, *args, **kwargs):
        self.validCategory = True
        self.article = article
        self.request = request
        super(SidebarForm, self).__init__(*args, **kwargs)
        self.fields['categories'].required = False
        self.fields['categories'].label_from_instance = lambda obj: mark_safe("%s" % obj.short_title + (' <a href=/'+obj.slug+' target="_blank">View</a>'))
        self.fields['categories'].initial = article.categories.all
        self.fields['categories'].widget = forms.CheckboxSelectMultiple()
        self.fields['categories'].queryset = models.Category.objects.all()
        if not self.article.categories.all():
            self.validCategory = False


    def get_usermessage(self):
        return ugettext(
            "New category set.")

    def save(self, *args, **kwargs):
        if self.is_valid():
            data = self.cleaned_data
            field = data['categories']
            self.article.categories = field
            self.article.save()
        return super(SidebarForm, self).save(*args, **kwargs)

    class Meta:
        model = models.Article
        fields = ('categories',)

class EditCategoryForm(PluginSidebarFormMixin, forms.ModelForm):


    ''' This edit form allows us to change the parent category of a category
        via the edit screen of its category landing article'''

    def __init__(self, article, request, *args, **kwargs):
        self.validCategory = True
        self.article = article
        self.request = request
        super(EditCategoryForm, self).__init__(*args, **kwargs)
        self.fields['parent'].label_from_instance = lambda obj: mark_safe("%s" %  obj.parent.short_title + '--->' + obj.short_title if not obj.parent is None else obj.short_title)
        try:
            self.fields['parent'].initial = self.article.categories.all()[0].parent
        except:
            if not self.article.categories.all():
                self.validCategory = False
            pass

        # logic to remove the category itself and its children from the available choices
        # to avoid edge cases

        for category in article.categories.all():
            ids = []
            cat_children = []
            try:
                for child in category.children.all():
                    cat_children.append(child)
            except:
                pass
            while cat_children:
                for child in cat_children:
                    try:
                        for children in child.children.all():
                            cat_children.append(children)
                    except:
                        pass
                    ids.append(child.id)
                    cat_children.remove(child)
            self.fields['parent'].queryset = models.Category.objects.exclude(id__in = ids).exclude(slug = category.slug)

    def save(self, *args, **kwargs):
        self.instance = self.article.categories.all()[0]
        data = self.cleaned_data
        self.instance.parent = data['parent']
        self.instance.save()
        super(EditCategoryForm, self).save(*args, **kwargs)

    class Meta:
        model = models.Category
        fields = ('parent',)