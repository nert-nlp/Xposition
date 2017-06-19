from django.shortcuts import redirect
from . import models
from wiki.models import URLPath, Article, Category
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

    form_class = forms.MetadataForm
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

    def get_forms(self):
        form = [super(MetadataView, self).get_form(form_class=forms.MetadataForm),
                super(MetadataView, self).get_form(form_class=forms.SupersenseForm)]
        return form

    def get_context_data(self, **kwargs):
        kwargs = super(MetadataView, self).get_context_data(**kwargs)
        kwargs['form_choices'] = ["Metadata", "Supersense"]
        kwargs['forms'] = self.get_forms()
        kwargs['article'] = self.article
        return kwargs

    def form_valid(self, form):
        self.article_urlpath = URLPath.create_article(
            URLPath.root(),
            form.data['name'],
            title=form.data['name'],
            content=form.data['description'],
            user_message=" ",
            user=self.request.user,
            article_kwargs={'owner': self.request.user,
                            'group': self.article.group,
                            'group_read': self.article.group_read,
                            'group_write': self.article.group_write,
                            'other_read': self.article.other_read,
                            'other_write': self.article.other_write,
                            })
        if 'supersense' in form.data:
            self.metadata = models.Supersense.objects.create(name = form.data['name'],
                                                             description = form.data['description'],
                                                             animacy = form.data['animacy'],
                                                             counterpart = form.data['counterpart'])
        elif 'metadata' in form.data:
            self.metadata = models.Metadata.objects.create(name = form.data['name'],
                                                           description = form.data['description'])
        self.metadata.article = Article.objects.get(urlpath = self.article_urlpath)
        if 'supersense' in form.data:
            self.supersense_category = Category.objects.create(slug = form.data['name'],
                                                                name = form.data['name'],
                                                                description = form.data['description'])
            self.metadata.article.categories.add(self.supersense_category)
        self.metadata.save()
        return redirect(
            "wiki:get",
            path=self.article_urlpath.path,
            article_id=self.article.id)

    def processSupersense(self, data):
        1+1

    def processMetadata(self, data):
        2+2

