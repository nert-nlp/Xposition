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
    from django.views.generic import DetailView, ListView, FormView, TemplateView
except ImportError:
    try:
        from cbv import DetailView, ListView, FormView, TemplateView
    except ImportError:
        from django.core.exceptions import ImproperlyConfigured
        raise ImproperlyConfigured("For older versions of Django, you need django-cbv.")

class ArticleMetadataView(ArticleMixin, FormView):
    """Base class for a view of a form for the metadata associated with an article."""

    template_name = "metadataform.html"
    edit = False

    def __init__(self, *args, edit=False, **kwargs):
        self.edit = edit    # creating a new instance or editing an existing one?
        super(ArticleMetadataView, self).__init__(*args, **kwargs)

    @method_decorator(get_article(can_read=True))
    def dispatch(self, request, article, *args, **kwargs):
        return super(ArticleMetadataView, self).dispatch(request, article, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super(ArticleMetadataView, self).get_form_kwargs()
        kwargs['article'] = self.article
        kwargs['request'] = self.request
        if self.edit:
            model_class = self.get_model_class_with_article()
            model_instance_with_article = model_class.objects.get(article = self.article)
            if hasattr(model_instance_with_article, 'current_revision'):
                kwargs['instance'] = models.deepest_instance(model_instance_with_article.current_revision)
            else:
                kwargs['instance'] = model_instance_with_article
            kwargs['initial'] = self.get_extra_data(kwargs['instance'])
        return kwargs

    def get_model_class_with_article(self):
        return self.form_class._meta.model

    def get_extra_data(self, instance):
        """Override to recover saved data that is not directly in the instance,
        but is displayed on the form."""
        return {}

    def get_context_data(self, **kwargs):
            # Needed since Django 1.9 because get_context_data is no longer called
            # with the form instance
            kwargs['form_heading'] = self.form_heading
            if 'form' not in kwargs:
                kwargs['form'] = self.get_form()
            return super(ArticleMetadataView, self).get_context_data(**kwargs)

    def form_valid(self, form):
        self.success_url = form.save()
        super(ArticleMetadataView, self).form_valid(form)
        return redirect("wiki:get", path=self.success_url)

class LanguageView(ArticleMetadataView):
    form_class = forms.LanguageForm
    form_heading = 'Create Language'

class SupersenseView(ArticleMetadataView):
    form_class = forms.SupersenseForm
    form_heading = 'Create Supersense'

    def get_model_class_with_article(self):
        return models.Supersense

    def get_extra_data(self, instance):
        article = instance.supersense.article
        urlpath = article.urlpath_set.all()[0]
        return {'slug': urlpath.slug}

class MetadataView(ArticleMixin, TemplateView):
    template_name = "metadata.html"

    @method_decorator(get_article(can_read=True))
    def dispatch(self, request, article, *args, **kwargs):
        return super(MetadataView, self).dispatch(request, article, *args, **kwargs)

    def get_context_data(self, **kwargs):
        return ArticleMixin.get_context_data(self, **kwargs)

    # def get_context_data(self, **kwargs):
    #     kwargs = super(MetadataView, self).get_context_data(**kwargs)
    #
    #     # get form and insert into context
    #
    #     #kwargs['form'] = self.get_form()
    #     kwargs['article'] = self.article
    #     kwargs['request'] = self.request
    #     return kwargs

# class MetadataView(ArticleMixin, FormView):
#
#
#     ''' View used to generate forms and process new metadata creation via the metadata 'tab' '''
#
#     template_name = "metadata.html"
#     # metadata.html contains the template for displaying the metadata creation forms
#
#     @method_decorator(get_article(can_read=True, can_create=True), )
#     def dispatch(self, request, article, *args, **kwargs):
#
#         return super(
#             MetadataView,
#             self).dispatch(
#             request,
#             article,
#             *args,
#             **kwargs)
#
#     def get_form_kwargs(self, **kwargs):
#         kwargs = super(MetadataView, self).get_form_kwargs(**kwargs)
#         kwargs['article'] = self.article
#         kwargs['request'] = self.request
#         return kwargs
#
#
#     # To add a new type of metadata creation, create a form and return it in this array
#
#     def get_forms(self):
#         kwargs = self.get_form_kwargs()
#         form = [super(MetadataView, self).get_form(form_class=forms.MetadataForm),
#                 super(MetadataView, self).get_form(form_class=forms.SupersenseForm),
#                 super(MetadataView, self).get_form(form_class=forms.LanguageForm),
#                 super(MetadataView, self).get_form(form_class=forms.ExampleForm)]
#         return form
#
#     def get_context_data(self, **kwargs):
#         kwargs = super(MetadataView, self).get_context_data(**kwargs)
#
#         # get forms and insert into context
#
#         kwargs['forms'] = self.get_forms()
#         kwargs['article'] = self.article
#         return kwargs
#
#
#     def get_object(self):
#         return get_object_or_404(wiki.models.Model, pk=self.request.session['value_here'])
#
#
#
#     # This is where form validation is done, we process the form and create the new metadata here
#
#     # Handle submission from one of the forms on the multiform page.
#     # See https://stackoverflow.com/a/30116519
#     def post(self, form, *args, **kwargs):
#         self.object = self.get_object()
#
#         metadataForm = self.get_form(forms.MetadataForm)
#         supersenseForm = self.get_form(forms.SupersenseForm)
#         langForm = self.get_form(forms.LanguageForm)
#         chosenForm = None
#         if 'supersense' in supersenseForm.data:
#             chosenForm = supersenseForm
#             chosenForm.prefix = 'supersense'
#         elif 'name' in langForm.data:
#             chosenForm = langForm
#             chosenForm.prefix = 'language'
#         else:
#             chosenForm = metadataForm
#             chosenForm.prefix = 'meta'
#
#         if not chosenForm.is_valid():
#             x = chosenForm.errors
#             1/0
#             return self.form_invalid(chosenForm, **kwargs)
#
#         self.article_urlpath = chosenForm.save()
#
#         return redirect(
#                 "wiki:get",
#                 path=self.article_urlpath.path,
#                 article_id=self.article.id)
#
#     def form_invalid(self, problem_form, **kwargs):
#         p = problem_form.prefix
#         return self.render_to_response(self.get_context_data(**{problem_form.prefix: problem_form,
#             'expand_'+problem_form.prefix: 'expand'}))
