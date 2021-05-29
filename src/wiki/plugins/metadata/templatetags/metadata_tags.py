from django import template
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import F, Q, Count, Min, URLField
from django.utils.safestring import mark_safe
from django.utils.html import conditional_escape, format_html
from django_tables2 import RequestConfig
from bitfield import BitField
from wiki.models import Article, ArticleRevision
from wiki.models.pluginbase import RevisionPlugin, RevisionPluginRevision
from wiki.plugins.metadata.models import MetadataRevision, SimpleMetadata, Supersense, Construal, Language, Corpus, Adposition, AdpositionRevision, Usage, UsageRevision, PTokenAnnotation, deepest_instance
from wiki.plugins.metadata.tables import PTokenAnnotationTable
from categories.models import Category

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
                display += v.html() if callable(v.html) else v.html
            elif hasattr(fld, 'choices') and fld.choices:
                choices = dict(fld.choices)
                if v is not None:   # if None, display nothing
                    v = str(choices[int(v)])
                    display += str(v)
            elif isinstance(fld, BitField):
                display += ', '.join(case for case,allowed in v if allowed)
            elif isinstance(fld, URLField):
                display += format_html('<a href="{}">{}</a>', v, v)
            elif fld.name=='description' and hasattr(meta, 'descriptionhtml'):
                display += meta.descriptionhtml()
            else:
                display += str(v)
            display += '</td></tr>\n'
    display += '</table>'
    display += '<!--'+str(meta)+'-->'
    return mark_safe(display)


@register.simple_tag(takes_context=True)
def langs_display(context):
    """Display a list of languages recorded in the database."""
    if 'article' not in context:
        return ''

    article = context['article']
    s = ''
    for lang in Language.with_nav_links().order_by('name'):
        langart = lang.article
        s += '<li'
        if article==langart:
            s += ' class="active"'
        s += '><a href="' + langart.get_absolute_url() + '">' + lang.name + '</a></li>'
    return mark_safe(s)

@register.simple_tag(takes_context=True)
def adpositions_for_lang(context):
    context['always_transitive'] = Adposition.Transitivity.always_transitive
    context['sometimes_transitive'] = Adposition.Transitivity.sometimes_transitive
    context['always_intransitive'] = Adposition.Transitivity.always_intransitive
    larticle = context['article']
    a = Adposition.objects.select_related('article').prefetch_related('current_revision__metadatarevision__adpositionrevision__lang',
        'article__urlpath_set').filter(current_revision__metadatarevision__adpositionrevision__lang__article=larticle,
            article__current_revision__deleted=False)
    a = a.annotate(transliteration=F('current_revision__metadatarevision__adpositionrevision__transliteration'),
                   num_usages=Count('usages__construal',distinct=True))
    context['swps'] = a.filter(current_revision__metadatarevision__adpositionrevision__is_pp_idiom=False).exclude(
        current_revision__metadatarevision__name__contains='_')
    context['mwps'] = a.filter(current_revision__metadatarevision__adpositionrevision__is_pp_idiom=False,
        current_revision__metadatarevision__name__contains='_')
    context['ppidioms'] = a.filter(current_revision__metadatarevision__adpositionrevision__is_pp_idiom=True)
    context['misc'] = a.exclude(current_revision__metadatarevision__adpositionrevision__is_pp_idiom__in=(True,False))

    urs = UsageRevision.objects.filter(adposition__in=a, plugin_set__article__current_revision__deleted=False)
    cc = Construal.objects.filter(usages__in=urs).distinct()
    context['construals'] = cc    # construals attested in this language
    return a

@register.simple_tag(takes_context=True)
def usages_for_lang(context):
    article = context['article']
    u = Usage.objects.filter(current_revision__metadatarevision__usagerevision__adposition__current_revision__metadatarevision__adpositionrevision__lang__article=article,
        current_revision__metadatarevision__article_revision__deleted=False)
    return u

@register.simple_tag(takes_context=True)
def corpora_for_lang(context):
    article = context['article']
    cc = Corpus.objects.filter(article__current_revision__deleted=False)
    return [c for c in cc if c.article.urlpath_set.all()[0].parent.article==article]

@register.simple_tag(takes_context=True)
def corpus_stats(context):
    article = context['article']
    c = Corpus.objects.get(article=article)
    nSents = c.corpus_sentences.count()
    nDocs = c.corpus_sentences.aggregate(num_docs=Count('doc_id', distinct=True))['num_docs']
    nWords = sum(len(sent.tokens) for sent in c.corpus_sentences.all())
    nAdpToks = PTokenAnnotation.objects.filter(sentence__corpus=c).count()
    adptypes = Adposition.objects.select_related('current_revision__metadatarevision').prefetch_related('article__urlpath_set__parent').annotate(adposition_freq=Count('ptokenannotation', filter=Q(ptokenannotation__sentence__corpus=c))).filter(adposition_freq__gt=0).order_by('-adposition_freq', 'current_revision__metadatarevision__name')
    context['adpositions_freq'] = adptypes
    #adpconst = Adposition.objects.annotate(adposition_nconst=Count('ptokenannotation__usage', distinct=True, filter=Q(sentence__corpus=c))).order_by('-adposition_nconst', 'current_revision__metadatarevision__name')
    #context['adpositions_nconstruals'] = adpconst
    usages = Usage.objects.select_related('current_revision__metadatarevision__usagerevision__article_revision__article__current_revision',
        #'current_revision__metadatarevision__usagerevision__article_revision__article__owner',
        'current_revision__metadatarevision__usagerevision__adposition__current_revision__metadatarevision',
        'current_revision__metadatarevision__usagerevision__construal__role__current_revision__metadatarevision',
        'current_revision__metadatarevision__usagerevision__construal__function__current_revision__metadatarevision').prefetch_related('current_revision__metadatarevision__usagerevision__article_revision__article__urlpath_set__parent').annotate(usage_freq=Count('ptokenannotation', filter=Q(ptokenannotation__sentence__corpus=c))).filter(usage_freq__gt=0).order_by('-usage_freq', 'current_revision__metadatarevision__name')
    context['usages_freq'] = usages
    construals = Construal.objects.select_related('article__current_revision',
        'role__current_revision__metadatarevision',
        'function__current_revision__metadatarevision').annotate(construal_freq=Count('ptoken_with_construal', filter=Q(ptoken_with_construal__sentence__corpus=c))).filter(construal_freq__gt=0).order_by('-construal_freq', 'special', 'role', 'function')
    context['construals_freq'] = construals
    ssr = Supersense.objects.select_related('article__current_revision', 'current_revision__metadatarevision').annotate(role_freq=Count('rfs_with_role__ptoken_with_construal', filter=Q(rfs_with_role__ptoken_with_construal__sentence__corpus=c))).order_by('-role_freq', 'current_revision__metadatarevision__name')
    ssf = Supersense.objects.select_related('article__current_revision', 'current_revision__metadatarevision').annotate(fxn_freq=Count('rfs_with_function__ptoken_with_construal', filter=Q(rfs_with_function__ptoken_with_construal__sentence__corpus=c))).order_by('-fxn_freq', 'current_revision__metadatarevision__name')
    context['ss_role_freq'] = ssr
    context['ss_fxn_freq'] = ssf
    s = f'''<table id="stats" class="table text-right">
                <tr><th>&nbsp;</th><th>Tokens</th><th>Types</th></tr>
                <tr><th>Documents</th><td>{nDocs}</td></tr>
                <tr><th>Sentences</th><td>{nSents}</td></tr>
                <tr><th>Words</th><td>{nWords}</td></tr>
                <tr><th>Adpositions</th><td>{nAdpToks}</td><td>{adptypes.count()}</tr>
                <tr><th>Usages</th><td></td><td>{usages.count()}</tr>
                <tr><th>Construals</th><td></td><td>{construals.count()}</tr>
            </table>'''
    if c.deprecated:
        s = '<div class="alert alert-warning">\n' \
            '<h4>There is a newer version of this corpus. Annotations from this version will not appear on documentation pages by default.</h4>\n' \
            '</div>\n\n'+s

    return mark_safe(s)

@register.simple_tag(takes_context=True)
def usagerevs_for_adp(context):
    particle = context['article']
    u = UsageRevision.objects.select_related('adposition__current_revision__metadatarevision',
        'construal__role__current_revision__metadatarevision',
        'construal__function__current_revision__metadatarevision').filter(adposition__article=particle,
        article_revision__deleted=False,
        article_revision__article__current_revision=F('article_revision'))  # ensure this isn't an outdated revision
    return u

@register.simple_tag(takes_context=True)
def usagerevs_for_construal(context):
    carticle = context['article']
    u = UsageRevision.objects.select_related('adposition__current_revision__metadatarevision',
        'construal__role__current_revision__metadatarevision',
        'construal__function__current_revision__metadatarevision').filter(construal__article=carticle,
        article_revision__deleted=False,
        article_revision__article__current_revision=F('article_revision'))  # ensure this isn't an outdated revision
    return u

def paginate(items, context):
    request = context['request']
    """"
    perpage = request.GET.get('perpage', 25)
    if int(perpage)<0: perpage = 10000 # practically no limit
    page = request.GET.get('page', 1)
    context['page'] = page
    context['perpage'] = perpage
    paginator = Paginator(items, perpage)
    context['pag'] = paginator
    """
    table = PTokenAnnotationTable(items)
    RequestConfig(request, paginate={'per_page': 25}).configure(table)
    context['tokstable'] = table
    return table

@register.simple_tag(takes_context=True)
def token_by_exnum(context):
    exnum = int(context['exnum'])
    t = PTokenAnnotation.objects.filter(id=exnum-3000)
    return paginate(t, context)

@register.simple_tag(takes_context=True)
def tokens_by_sentid(context):
    sentid = context['sent_id']
    corpus_name = context['corpus']
    corpora = Corpus.objects.all()
    corpus = [c for c in corpora if str(c)==corpus_name][0]
    t = PTokenAnnotation.objects.filter(sentence__sent_id=sentid, sentence__corpus=corpus).order_by('id')
    if not t:
        raise Exception(f'Sent id "{sentid}" in {corpus_name} does not exist.')
    context['sentence'] = t[0].sentence
    return paginate(t, context)

@register.simple_tag(takes_context=False)
def split(s):
    return s.split(' ')

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

@register.simple_tag(takes_context=False)
def truncate_contents_after_colon(s):
    i = s.index('>')+1
    j = s.index('</', i)
    c = s.index(':', i)
    return s[:c] + s[j:]

@register.simple_tag(takes_context=False)
def all_p_tokens_in_sentence(sentence):
    pts = sentence.ptokenannotation_set.all()
    result = {}
    for pt in pts:
        assert pt.main_subtoken_indices[0] not in result
        assert pt.main_subtoken_indices[-1] not in result
        result[pt.main_subtoken_indices[0]] = pt # open the link
        result[pt.main_subtoken_indices[-1]] = pt    # close the link
    return result

@register.simple_tag(takes_context=False)
def other_p_tokens_in_sentence(pt):
    others = pt.sentence.ptokenannotation_set.exclude(pk=pt.pk)
    result = {}
    for opt in others:
        assert opt.main_subtoken_indices[0] not in result
        assert opt.main_subtoken_indices[-1] not in result
        result[opt.main_subtoken_indices[0]] = opt # open the link
        result[opt.main_subtoken_indices[-1]] = opt    # close the link
    return result

def _category_subtree(c, recursive=False):
    ss = c.supersense.all()[0]
    a = ss.article
    #s = '<li><a href="{url}">{rev}</a>'.format(url=a.get_absolute_url(), rev=a.current_revision.title)
    s = f'<li class="clt">{ss.html}' if not recursive else f'<li>{ss.html}'
    # number of construals for the supersense
    nAsRole = len(ss.rfs_with_role.all())
    nAsFunction = len(ss.rfs_with_function.all())
    s += ' <small style="font-size: 50%;">{}<span style="color: #999;" class="construal-arrow">&#x219d;</span>{}</small>'.format(nAsRole, nAsFunction)
    #print(s)
    children = c.children.all() #.filter(current_revision__metadatarevision__article_revision__deleted=False)
    #print(children)
    if len(children):
        s += '\n<ul>'
        for child in children:
            s += _category_subtree(child, recursive=True)
        s += '\n</ul>'
    s += '</li>'
    return s

@register.simple_tag(takes_context=True)
def supersenses_display(context, top):
    """Display a list of supersenses recorded in the database."""
    try:
        t = Supersense.objects.get(current_revision__metadatarevision__name=top)
		# address issue #33
        #t = t.filter(current_revision__metadatarevision__article_revision__deleted=False)
        return mark_safe(_category_subtree(t.category))
    except Exception as ex:
        return 'NOT FOUND'

@register.simple_tag(takes_context=True)
def construals_display(context, role=None, function=None, order_by='role' or 'function'):
    """Display a list of construals recorded in the database."""
    order_by2 = 'role' if order_by=='function' else 'function'
    s = ''
    cc = Construal.objects.select_related('article__current_revision', # to speed up c.html below
            'role__current_revision__metadatarevision',
            'function__current_revision__metadatarevision').filter(article__current_revision__deleted=False)
    if role is not None:
        cc = cc.filter(role__current_revision__metadatarevision__name=role)
    if function is not None:
        cc = cc.filter(function__current_revision__metadatarevision__name=function)

    for c in cc.order_by(order_by+'__current_revision__metadatarevision__name',
                         order_by2+'__current_revision__metadatarevision__name'):
        #a = c.article
        #s += '<li><a href="{url}">{rev}</a></li>\n'.format(url=a.get_absolute_url(), rev=a.current_revision.title)
        nadps = Usage.objects.filter(current_revision__metadatarevision__usagerevision__construal=c,
                                     article__current_revision__deleted=False).count()
        # NOT c.usages, which consists of all UsageRevisions
        s += f'<li>{c.html} (<span class="nadpositions' + (' major' if nadps>=10 else '') + f'">{nadps}</span>)</li>\n'
    return mark_safe(s)
