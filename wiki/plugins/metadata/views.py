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


    ''' View used to generate forms and process new metadata creation via the metadata 'tab' '''

    form_class = forms.MetadataForm
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
        return kwargs


    # To add a new type of metadata creation, create a form and return it in this array

    def get_forms(self):
        form = [super(MetadataView, self).get_form(form_class=forms.MetadataForm),
                super(MetadataView, self).get_form(form_class=forms.SupersenseForm)]
        return form

    def get_context_data(self, **kwargs):
        kwargs = super(MetadataView, self).get_context_data(**kwargs)

        # get forms and insert into context

        kwargs['forms'] = self.get_forms()
        kwargs['article'] = self.article
        return kwargs



    # This is where form validation is done, we process the form and create the new metadata here

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

        # if we are dealing with a base metadata object
        if 'metadata' in form.data:
            self.metadata = models.Metadata.objects.create(name = form.data['name'],
                                                           description = form.data['description'])
            self.metadata.article = Article.objects.get(urlpath=self.article_urlpath)


        # if supersense create a category and update counterpart if necessary
        if 'supersense' in form.data:
            self.metadata = models.Supersense.objects.create(name=form.data['name'],
                                                             description=form.data['description'],
                                                             animacy=form.data['animacy'],
                                                             template="supersense_article_view.html",
                                                             counterpart=None)
            if form.data['counterpart']:
                counterpart = models.Supersense.objects.get(name=form.data['counterpart'])
                self.metadata.counterpart = counterpart
                counterpart.counterpart = self.metadata
                counterpart.save()
            else:
                pass
            supersense_category = Category.objects.create(slug = form.data['name'],
                                                                name = form.data['name'],
                                                                description = form.data['description'])
            self.metadata.article = Article.objects.get(urlpath=self.article_urlpath)
            self.metadata.article.categories.add(supersense_category)

        #if adding a new metadata type, include save logic here. MAKE SURE TO INCLUDE YOUR CUSTOM METADATA TEMPLATE IN CREATION, SEE ABOVE

        self.metadata.save()
        return redirect(
            "wiki:get",
            path=self.article_urlpath.path,
            article_id=self.article.id)


