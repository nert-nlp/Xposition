from django.shortcuts import redirect
from wiki.models import URLPath, Article, Category
from django.utils.decorators import method_decorator
from wiki.views.mixins import ArticleMixin
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

    template_name = "metadata.html"

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
        return kwargs


    def get_context_data(self, **kwargs):
        kwargs = super(MetadataView, self).get_context_data(**kwargs)
        kwargs['article'] = self.article
        return kwargs