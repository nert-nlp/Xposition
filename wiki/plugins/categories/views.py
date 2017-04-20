from django.shortcuts import redirect
from wiki.models import URLPath, Article, Category
from django.views.generic.edit import FormView
from django.forms import modelform_factory
from wiki.views.mixins import ArticleMixin
from django.utils.decorators import method_decorator
from wiki.conf import settings as wiki_settings
from wiki.decorators import get_article
from wiki.models.pluginbase import RevisionPluginRevision
from wiki.views.mixins import ArticleMixin
from django.views.generic.list import MultipleObjectMixin
from django.shortcuts import get_object_or_404
from django.core.exceptions import ObjectDoesNotExist
from django.template import RequestContext
from django.http import HttpResponse, Http404
from django.template.loader import select_template
from django.utils.translation import ugettext_lazy as _
try:
    from django.views.generic import DetailView, ListView
except ImportError:
    try:
        from cbv import DetailView, ListView
    except ImportError:
        from django.core.exceptions import ImproperlyConfigured
        raise ImproperlyConfigured("For older versions of Django, you need django-cbv.")


from . import forms

def category_detail(request, path, template_name='categories/category_detail.html', extra_context={}):
    path_items = path.strip('/').split('/')
    if len(path_items) >= 2:
        category = get_object_or_404(
            Category,
            slug__iexact=path_items[-1],
            level=len(path_items) - 1,
            parent__slug__iexact=path_items[-2])
    else:
        category = get_object_or_404(
            Category,
            slug__iexact=path_items[-1],
            level=len(path_items) - 1)

    templates = []
    while path_items:
        templates.append('categories/%s.html' % '_'.join(path_items))
        path_items.pop()
    templates.append(template_name)

    context = RequestContext(request)
    context.update({'category': category})
    if extra_context:
        context.update(extra_context)
    return HttpResponse(select_template(templates).render(context))


def get_category_for_path(path, queryset=Category.objects.all()):
    path_items = path.strip('/').split('/')
    if len(path_items) >= 2:
        queryset = queryset.filter(
            slug__iexact=path_items[-1],
            level=len(path_items) - 1,
            parent__slug__iexact=path_items[-2])
    else:
        queryset = queryset.filter(
            slug__iexact=path_items[-1],
            level=len(path_items) - 1)
    return queryset.get()


class CategoryDetailView(DetailView):
    model = Category
    path_field = 'path'

    def get_object(self, **kwargs):
        if self.path_field not in self.kwargs:
            raise AttributeError("Category detail view %s must be called with "
                                 "a %s." % self.__class__.__name__, self.path_field)
        if self.queryset is None:
            queryset = self.get_queryset()
        try:
            return get_category_for_path(self.kwargs[self.path_field], self.model.objects.all())
        except ObjectDoesNotExist:
            raise Http404(_("No %(verbose_name)s found matching the query") %
                          {'verbose_name': queryset.model._meta.verbose_name})

    def get_template_names(self):
        names = []
        path_items = self.kwargs[self.path_field].strip('/').split('/')
        while path_items:
            names.append('categories/%s.html' % '_'.join(path_items))
            path_items.pop()
        names.extend(super(CategoryDetailView, self).get_template_names())
        return names


class CategoryRelatedDetail(DetailView):
    path_field = 'category_path'
    object_name_field = None

    def get_object(self, **kwargs):
        queryset = super(CategoryRelatedDetail, self).get_queryset()
        category = get_category_for_path(self.kwargs[self.path_field])
        return queryset.get(category=category, slug=self.kwargs[self.slug_field])

    def get_template_names(self):
        names = []
        opts = self.object._meta
        path_items = self.kwargs[self.path_field].strip('/').split('/')
        if self.object_name_field:
            path_items.append(getattr(self.object, self.object_name_field))
        while path_items:
            names.append('%s/category_%s_%s%s.html' % (
                opts.app_label,
                '_'.join(path_items),
                opts.object_name.lower(),
                self.template_name_suffix)
            )
            path_items.pop()
        names.append('%s/category_%s%s.html' % (
            opts.app_label,
            opts.object_name.lower(),
            self.template_name_suffix)
        )
        names.extend(super(CategoryRelatedDetail, self).get_template_names())
        return names


class CategoryRelatedList(ListView):
    path_field = 'category_path'

    def get_queryset(self):
        queryset = super(CategoryRelatedList, self).get_queryset()
        category = get_category_for_path(self.kwargs['category_path'])
        return queryset.filter(category=category)

    def get_template_names(self):
        names = []
        if hasattr(self.object_list, 'model'):
            opts = self.object_list.model._meta
            path_items = self.kwargs[self.path_field].strip('/').split('/')
            while path_items:
                names.append('%s/category_%s_%s%s.html' % (
                    opts.app_label,
                    '_'.join(path_items),
                    opts.object_name.lower(),
                    self.template_name_suffix)
                )
                path_items.pop()
            names.append('%s/category_%s%s.html' % (
                opts.app_label,
                opts.object_name.lower(),
                self.template_name_suffix)
            )
        names.extend(super(CategoryRelatedList, self).get_template_names())
        return names


class CategoryView( ArticleMixin, FormView ):

    form_class = forms.CategoryForm
    template_name = "category_detail.html"

    @method_decorator(get_article(can_read=True, can_create=True),)
    def dispatch(self, request, article, *args, **kwargs):
        self.categories = Category.objects.all()
        return super(
            CategoryView,
            self).dispatch(
            request,
            article,
            *args,
            **kwargs)

    def get_form_kwargs(self, **kwargs):
        kwargs = super(CategoryView, self).get_form_kwargs(**kwargs)
        return kwargs

    def form_valid(self, form):
        clean_data = form.cleaned_data
        print(clean_data)
        slug = clean_data['slug']
        title = clean_data['name']
        content = clean_data['description']
        self.landing_article_urlpath = URLPath.create_article(
            URLPath.root(),
            slug,
            title = title,
            content = content,
            user_message = " ",
            user = self.request.user,
            article_kwargs = {'owner': self.request.user,
                              'group': self.article.group,
                              'group_read': self.article.group_read,
                              'group_write': self.article.group_write,
                              'other_read': self.article.other_read,
                              'other_write': self.article.other_write,
                              })
        form.save()
        category = Category.objects.get(name = title)
        landing_article = Article.objects.get(urlpath = self.landing_article_urlpath)
        landing_article.categories.add(category)
        self.landing_article_urlpath.save()
        return redirect(
            "wiki:get",
            path=self.landing_article_urlpath.path,
            article_id=self.article.id)

    def get_form(self):
        form = super(CategoryView, self).get_form(form_class=forms.CategoryForm)
        return form


    def get_edit_form(self):
        form = super(CategoryView, self).get_form(form_class=forms.CategoryForm)
        form.instance = self.article.categories.objects.filter(slug = self.urlpath.slug)
        return form

    def get_context_data(self, **kwargs):
        kwargs['categories'] = Category.objects.all()
        kwargs['form'] = self.get_form()
        kwargs['edit_form'] = 0
        kwargs = super(CategoryView, self).get_context_data(**kwargs)
        kwargs['article'] = self.article
        return kwargs
