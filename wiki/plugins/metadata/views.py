from django.shortcuts import redirect
from . import models
from wiki.models import URLPath, Article
from wiki.plugins.categories.models import ArticleCategory
from django.utils.decorators import method_decorator
from wiki.views.mixins import ArticleMixin
from . import forms
from wiki.decorators import get_article
try:
    from django.views.generic import DetailView, ListView, FormView
except ImportError:
    try:
        from cbv import DetailView, ListView, FormView
    except ImportError:
        from django.core.exceptions import ImproperlyConfigured
        raise ImproperlyConfigured("For older versions of Django, you need django-cbv.")



class MetadataView(ArticleMixin, FormView):


    ''' View used to generate forms and process new metadata creation via the metadata 'tab' '''

    template_name = "metadata.html"
    # metadata.html contains the template for displaying the metadata creation forms

    @method_decorator(get_article(can_read=True, can_create=True), )
    def dispatch(self, request, article, *args, **kwargs):

        return super(
            MetadataView,
            self).dispatch(
            request,
            article,
            *args,
            **kwargs)

    def get_form_kwargs(self, **kwargs):
        kwargs = super(MetadataView, self).get_form_kwargs(**kwargs)
        kwargs['article'] = self.article
        kwargs['request'] = self.request
        return kwargs


    # To add a new type of metadata creation, create a form and return it in this array

    def get_forms(self):
        kwargs = self.get_form_kwargs()
        form = [super(MetadataView, self).get_form(form_class=forms.MetadataForm),
                super(MetadataView, self).get_form(form_class=forms.SupersenseForm),
                super(MetadataView, self).get_form(form_class=forms.ExampleForm)]
        return form

    def get_context_data(self, **kwargs):
        kwargs = super(MetadataView, self).get_context_data(**kwargs)

        # get forms and insert into context

        kwargs['forms'] = self.get_forms()
        kwargs['article'] = self.article
        return kwargs



    # This is where form validation is done, we process the form and create the new metadata here

    def post(self, form):
        metadataForm = self.get_form(forms.MetadataForm)
        supersenseForm = self.get_form(forms.SupersenseForm)
        if 'supersense' in supersenseForm.data:
            self.article_urlpath = supersenseForm.save()
        else:
            self.article_urlpath = metadataForm.save()
        # self.article_urlpath = form.save()
        # if we are dealing with a base metadata object
        return redirect(
            "wiki:get",
            path=self.article_urlpath.path,
            article_id=self.article.id)
