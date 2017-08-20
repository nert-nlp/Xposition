from django import template
from django.utils.safestring import mark_safe
from wiki.models import Article, ArticleRevision
from wiki.models.pluginbase import RevisionPlugin, RevisionPluginRevision
from wiki.plugins.metadata.models import MetadataRevision, SimpleMetadata, Language, deepest_instance

register = template.Library()

@register.simple_tag(takes_context=True)
def metadata_display(context, metadata):
    meta = deepest_instance(metadata)
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
    #display += str(meta) + '; ' + str(metadata)
    return mark_safe(display)


@register.simple_tag(takes_context=True)
def langs_display(context):
    """Display a list of languages recorded in the database."""
    article = context['article']
    s = ''
    for lang in Language.with_nav_links():
        langart = lang.article
        s += '<li'
        if context['article']==langart or (hasattr(article, 'metadata') and getattr(context['article'].metadata, 'language')==lang):
            s += ' class="active"'
        s += '><a href="' + langart.get_absolute_url() + '">' + lang.name + '</a></li>"'
    return mark_safe(s)
