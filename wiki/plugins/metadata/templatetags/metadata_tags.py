from django import template
from django.utils.safestring import mark_safe
from wiki.models import Article, ArticleRevision
from wiki.models.pluginbase import RevisionPlugin, RevisionPluginRevision
from wiki.plugins.metadata.models import MetadataRevision, SimpleMetadata, Supersense, Construal, Language, deepest_instance
from wiki.plugins.categories.models import Category

register = template.Library()

@register.simple_tag(takes_context=True)
def metadata_display(context):
    if 'article' not in context:
        return ''

    article = context['article']
    c = article.current_revision
    if hasattr(c, 'metadata_revision'):
        meta = deepest_instance(c.metadata_revision)
    else:
        articleplugins = [deepest_instance(z) for z in article.articleplugin_set.all()]
        meta = [z for z in articleplugins if isinstance(z, SimpleMetadata)]   # not Metadata, because that will have an article_revision pointer and be handled above
        assert 0<=len(meta)<=1
        if meta:
            meta = meta[0]
        else:
            return

    #meta = deepest_instance(metadata)
    #if hasattr(meta, 'current_revision'):
    #    meta = deepest_instance(meta.current_revision)
    generic_flds = MetadataRevision._meta.get_fields() + SimpleMetadata._meta.get_fields()
    display = '<h4 id="metadata">Metadata'
    if hasattr(meta, 'editurl'):
        editurl = meta.editurl(context['urlpath'])
        display += ' <a href="' + editurl + '" style="float: right;"><i class="fa fa-edit" alt="edit metadata"></i></a>'
    display += '</h4>\n<table class="metadata">\n'
    for fld in meta._meta.get_fields(include_hidden=False):
        if fld.name=='description' or fld not in generic_flds and not fld.name.endswith('_ptr'):
            display += f'    <tr><th style="padding: 10px;">{fld.name}</th><td>'
            v = getattr(meta, fld.name)
            if hasattr(v, 'html'):
                display += v.html()
            elif hasattr(fld, 'choices') and fld.choices:
                choices = dict(fld.choices)
                v = str(choices[int(v)])
                display += str(v)
            else:
                display += str(v)
            display += '</td></tr>\n'
    display += '</table>'
    display += str(meta)
    return mark_safe(display)


@register.simple_tag(takes_context=True)
def langs_display(context):
    """Display a list of languages recorded in the database."""
    if 'article' not in context:
        return ''

    article = context['article']
    s = ''
    for lang in Language.with_nav_links():
        langart = lang.article
        s += '<li'
        if context['article']==langart or (hasattr(article, 'metadata') and getattr(context['article'].metadata, 'language')==lang):
            s += ' class="active"'
        s += '><a href="' + langart.get_absolute_url() + '">' + lang.name + '</a></li>"'
    return mark_safe(s)

def _category_subtree(c):
    ss = c.supersense.all()[0]
    a = ss.article
    s = '<li><a href="{url}">{rev}</a>'.format(url=a.get_absolute_url(), rev=a.current_revision.title)
    # number of construals for the supersense
    nAsRole = len(ss.rfs_with_role.all())
    nAsFunction = len(ss.rfs_with_function.all())
    s += ' <small style="font-size: 50%;">{}<span style="color: #ccc;">~&gt;</span>{}</small>'.format(nAsRole, nAsFunction)
    #print(s)
    children = c.children.all()
    #print(children)
    if len(children):
        s += '\n<ul>'
        for child in children:
            s += _category_subtree(child)
        s += '\n</ul>'
    s += '</li>'
    return s

@register.simple_tag(takes_context=True)
def supersenses_display(context, top):
    """Display a list of supersenses recorded in the database."""
    try:
        t = Supersense.objects.get(current_revision__metadatarevision__name=top)
        return mark_safe(_category_subtree(t.category))
    except Exception as ex:
        return 'NOT FOUND'

@register.simple_tag(takes_context=True)
def construals_display(context, role=None, function=None, order_by='role' or 'function'):
    """Display a list of supersenses recorded in the database."""
    order_by2 = 'role' if order_by=='function' else 'function'
    s = ''
    cc = Construal.objects.all()
    if role is not None:
        cc = cc.filter(role__current_revision__metadatarevision__name=role)
    if function is not None:
        cc = cc.filter(function__current_revision__metadatarevision__name=function)
    for c in cc.order_by(order_by+'__current_revision__metadatarevision__name',
                         order_by2+'__current_revision__metadatarevision__name'):
        a = c.article
        s += '<li><a href="{url}">{rev}</a></li>\n'.format(url=a.get_absolute_url(), rev=a.current_revision.title)
    return mark_safe(s)
