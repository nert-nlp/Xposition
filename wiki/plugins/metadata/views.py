from django.shortcuts import redirect, get_object_or_404
from django.db.models import Model
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

class LanguageView(ArticleMixin, FormView):
    template_name = "metadataform.html"
    form_class = forms.LanguageForm
    #success_url =

    @method_decorator(get_article(can_read=True))
    def dispatch(self, request, article, *args, **kwargs):

        return super(
            LanguageView,
            self).dispatch(
            request,
            article,
            *args,
            **kwargs)

    def get_form_kwargs(self):
        kwargs = super(LanguageView, self).get_form_kwargs()
        kwargs['article'] = self.article
        kwargs['request'] = self.request
        return kwargs

    def get_context_data(self, **kwargs):
            # Needed since Django 1.9 because get_context_data is no longer called
            # with the form instance
            kwargs['form_heading'] = 'Create Language'
            if 'form' not in kwargs:
                kwargs['form'] = self.get_form()

            """
            kwargs['attachments'] = self.attachments
            kwargs['deleted_attachments'] = models.Attachment.objects.filter(
                articles=self.article,
                current_revision__deleted=True)
            kwargs['search_form'] = forms.SearchForm()
            kwargs['selected_tab'] = 'attachments'
            kwargs['anonymous_disallowed'] = self.request.user.is_anonymous(
            ) and not settings.ANONYMOUS
            """
            return super(LanguageView, self).get_context_data(**kwargs)

    def form_valid(self, form):
        self.success_url = form.save()
        super(LanguageView, self).form_valid(form)
        return redirect("wiki:get", path=self.success_url)

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
                super(MetadataView, self).get_form(form_class=forms.LanguageForm),
                super(MetadataView, self).get_form(form_class=forms.ExampleForm)]
        return form

    def get_context_data(self, **kwargs):
        kwargs = super(MetadataView, self).get_context_data(**kwargs)

        # get forms and insert into context

        kwargs['forms'] = self.get_forms()
        kwargs['article'] = self.article
        return kwargs


    def get_object(self):
        return get_object_or_404(wiki.models.Model, pk=self.request.session['value_here'])



    # This is where form validation is done, we process the form and create the new metadata here

    # Handle submission from one of the forms on the multiform page.
    # See https://stackoverflow.com/a/30116519
    def post(self, form, *args, **kwargs):
        self.object = self.get_object()

        metadataForm = self.get_form(forms.MetadataForm)
        supersenseForm = self.get_form(forms.SupersenseForm)
        langForm = self.get_form(forms.LanguageForm)
        chosenForm = None
        if 'supersense' in supersenseForm.data:
            chosenForm = supersenseForm
            chosenForm.prefix = 'supersense'
        elif 'name' in langForm.data:
            chosenForm = langForm
            chosenForm.prefix = 'language'
        else:
            chosenForm = metadataForm
            chosenForm.prefix = 'meta'

        if not chosenForm.is_valid():
            x = chosenForm.errors
            1/0
            return self.form_invalid(chosenForm, **kwargs)

        self.article_urlpath = chosenForm.save()

        return redirect(
                "wiki:get",
                path=self.article_urlpath.path,
                article_id=self.article.id)

    def form_invalid(self, problem_form, **kwargs):
        p = problem_form.prefix
        return self.render_to_response(self.get_context_data(**{problem_form.prefix: problem_form,
            'expand_'+problem_form.prefix: 'expand'}))
