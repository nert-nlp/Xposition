from django.db.models import Q
from django.http import Http404, HttpResponseBadRequest
from django.shortcuts import render
from django.utils.html import format_html, mark_safe
import django_tables2 as tables
from django_tables2 import RequestConfig

from .models import PTokenAnnotation,ParallelSentenceAlignment, ParallelPTokenAlignment

def other_p_tokens_in_sentence(pt):
    others = pt.sentence.ptokenannotation_set.exclude(pk=pt.pk)
    result = {}
    for opt in others:
        assert opt.main_subtoken_indices[0] not in result
        assert opt.main_subtoken_indices[-1] not in result
        result[opt.main_subtoken_indices[0]-1,opt.main_subtoken_indices[-1]] = opt # open the link
    return result


class ParallelSentenceAlignmentTable(tables.Table):


    exid = tables.Column(accessor='id',verbose_name='Alignment ID')
    source_sentence = tables.Column(accessor='source_sentence',verbose_name='Source Sentence ID')
    source_sentence_text = tables.Column(accessor='source_sentence.text', verbose_name="Source Sentence Text")
    source_sentence_language = tables.Column(accessor = 'source_sentence.language.name',verbose_name="Source Sentence Language")
    target_sentence = tables.Column(accessor='target_sentence',verbose_name='Sentence ID')
    target_sentence_text = tables.Column(accessor='target_sentence.text', verbose_name="Sentence Text")
    target_sentence_language = tables.Column(accessor='target_sentence.language.name', verbose_name="Sentence Language")

    def value_source_sentence(self, value):
        return value.sent_id

    def render_source_sentence(self, value):
        return value.html

    def value_target_sentence(self, value):
        return value.sent_id

    def render_target_sentence(self, value):
        return value.html


    class Meta:
        model = ParallelSentenceAlignment
        sequence = ('exid','source_sentence','source_sentence_language','source_sentence_text','target_sentence','target_sentence_language','target_sentence_text')
        template_name = 'django_tables2/bootstrap.html'
        attrs = {'class': 'table parallelsentencealignment'}



class PTokenAnnotationTable(tables.Table):
    """
    Note: the caller should use
        .select_related('construal__article__current_revision',
            'construal__role__article__current_revision', 'construal__function__article__current_revision',
            'usage__current_revision__metadatarevision__usagerevision__article_revision__article',
            'sentence', 'adposition')
    for efficiency (if those fields aren't being queried directly).
    """

    exid = tables.Column(accessor='id', verbose_name='Ex')
    lcontext = tables.Column(accessor='sentence.tokens', verbose_name='', attrs={'td': {'class': "lcontext"}})
    target = tables.Column(accessor='sentence.tokens', verbose_name='P', order_by=('adposition', 'construal'), attrs={'td': {'class': "construal"}})
    rcontext = tables.Column(accessor='sentence.tokens', verbose_name='', attrs={'td': {'class': "rcontext"}})
    role = tables.Column(accessor='construal.role', verbose_name='Role')
    construal = tables.Column(accessor='construal', verbose_name='↝', attrs={'td': {'class': "construal"}})
    function = tables.Column(accessor='construal.function', verbose_name='Function')
    note = tables.Column(accessor='annotator_cluster', verbose_name='ℹ')
    sentid = tables.Column(accessor='sentence', verbose_name='Sent ID')


    def render_exid(self, record):
        return record.html

    def value_lcontext(self, record, value):    # text only
        return ' '.join(value[:record.main_subtoken_indices[0]-1])

    def _gohead(self, i, pt, rhs=False):
        s = ''
        if i==pt.gov_head_index:
            s += 'govhead '
        if i==pt.obj_head_index:
            s += 'objhead '
        if rhs and i in pt.token_indices:   # for gappy multiword adpositions
            s += 'usage target '
        if s:
            s = s.strip()
            s = f' class="{s}"'
        return s

    def render_lcontext(self, record, value):
        tokens = [format_html('<span title="{}"' + self._gohead(q,record) + '>{}</span>', q, x) for q,x in enumerate(value[:record.main_subtoken_indices[0]-1], start=1)]
        spans_to_link = other_p_tokens_in_sentence(record)
        for (i,j),anno in sorted(spans_to_link.items(), reverse=True):
            if i<len(tokens):
                assert j<=len(tokens)
                tokens[i:j] = [anno.tokenhtml(offsets=True)]
        return mark_safe(' '.join(tokens))

    def value_target(self, record, value):
        tokens = value[record.main_subtoken_indices[0]-1:record.main_subtoken_indices[-1]]
        return ' '.join(tokens)

    def render_target(self, record, value):
        tokens = [format_html('<span title="{}">{}</span>', i+1, value[i]) for i in range(record.main_subtoken_indices[0]-1, record.main_subtoken_indices[-1])]
        usageurl = record.usage.current_revision.metadatarevision.usagerevision.url
        return mark_safe(f'<a href="{usageurl}" class="usage">' + ' '.join(tokens) + '</a>')

    def value_rcontext(self, record, value):   # text only
        return ' '.join(value[record.main_subtoken_indices[-1]:])

    def render_rcontext(self, record, value):
        h = record.main_subtoken_indices[-1]    # beginning of right context
        tokens = [format_html('<span title="{}"' + self._gohead(q,record,rhs=True) + '>{}</span>', q, x) for q,x in enumerate(value[h:], start=h+1)]
        spans_to_link = other_p_tokens_in_sentence(record)
        for (i,j),anno in sorted(spans_to_link.items(), reverse=True):
            assert i-h<len(tokens)
            if i>=h:
                assert j-h<=len(tokens)
                tokens[i-h:j-h] = [anno.tokenhtml(offsets=True)]
        return mark_safe(' '.join(tokens))

    def render_role(self, value):
        return value.html

    def render_function(self, value):
        return value.html

    def value_construal(self, value):
        return value if value.role is None else {True: '=', False: '≠'}[value.role==value.function]

    def render_construal(self, value):
        special = value.special and value.special.strip()
        return mark_safe(f'<a href="{value.url}" class="{"misc-label" if special else "construal"}">{self.value_construal(value)}</a>')

    def value_note(self, value):
        return value.strip()

    def render_note(self, value):
        v = self.value_note(value)
        if v:
            return format_html('<span title="{}" style="cursor: help">ℹ</span>', v)
        else:
            return ''

    def value_sentid(self, value):  # text only
        return value.sent_id

    def render_sentid(self, value):
        return value.html

    class Meta:
        model = PTokenAnnotation
        fields = ('adp_pos', 'gov_head', 'gov_pos', 'gov_supersense', 'obj_head', 'obj_pos', 'obj_supersense', 'gov_obj_syntax', 'is_transitive','is_typo','is_abbr')
        sequence = ('exid', 'lcontext', 'target', 'rcontext', 'role', 'construal', 'function', 'note') # columns to prepose
        template_name = 'django_tables2/bootstrap.html'
        attrs = {'class': 'table ptokenannotation'}


class ParallelPTokenAlignmentTable(tables.Table):

    sourceexid = tables.Column(accessor='source_example.id', verbose_name='Source Ex')
    targetexid = tables.Column(accessor='target_example.id', verbose_name='Ex')
    lcontext = tables.Column(accessor='target_example.sentence.tokens', verbose_name='')
    target = tables.Column(accessor='target_example.sentence.tokens', verbose_name='P', order_by=('target_example.adposition', 'target_example.construal'))
    rcontext = tables.Column(accessor='target_example.sentence.tokens', verbose_name='')
    role = tables.Column(accessor='target_example.construal.role', verbose_name='Role')
    construal = tables.Column(accessor='target_example.construal', verbose_name='↝')
    function = tables.Column(accessor='target_example.construal.function', verbose_name='Function')
    note = tables.Column(accessor='target_example.annotator_cluster', verbose_name='ℹ')
    sourcesentid = tables.Column(accessor='source_example.sentence', verbose_name='Source Sent ID')
    targetsentid = tables.Column(accessor='target_example.sentence', verbose_name='Sent ID')
    targetlanguage = tables.Column(accessor='target_example.sentence.language.name',verbose_name='Language')

    def render_sourceexid(self, record):
        return record.source_example.html

    def render_targetexid(self, record):
        return record.target_example.html

    def value_lcontext(self, record, value):  # text only
        return ' '.join(value[:record.target_example.main_subtoken_indices[0] - 1])

    def _gohead(self, i, pt, rhs=False):
        s = ''
        if i == pt.gov_head_index:
            s += 'govhead '
        if i == pt.obj_head_index:
            s += 'objhead '
        if rhs and i in pt.token_indices:  # for gappy multiword adpositions
            s += 'usage target '
        if s:
            s = s.strip()
            s = f' class="{s}"'
        return s

    def render_lcontext(self, record, value):
        tokens = [format_html('<span title="{}"' + self._gohead(q, record.target_example) + '>{}</span>', q, x) for q, x in
                  enumerate(value[:record.target_example.main_subtoken_indices[0] - 1], start=1)]
        spans_to_link = other_p_tokens_in_sentence(record.target_example)
        for (i, j), anno in sorted(spans_to_link.items(), reverse=True):
            if i < len(tokens):
                assert j <= len(tokens)
                tokens[i:j] = [anno.tokenhtml(offsets=True)]
        return mark_safe(' '.join(tokens))

    def value_target(self, record, value):
        tokens = value[record.target_example.main_subtoken_indices[0] - 1:record.target_example.main_subtoken_indices[-1]]
        return ' '.join(tokens)

    def render_target(self, record, value):
        tokens = [format_html('<span title="{}">{}</span>', i + 1, value[i]) for i in
                  range(record.target_example.main_subtoken_indices[0] - 1, record.target_example.main_subtoken_indices[-1])]
        usageurl = record.target_example.usage.current_revision.metadatarevision.usagerevision.url
        return mark_safe(f'<a href="{usageurl}" class="usage">' + ' '.join(tokens) + '</a>')

    def value_rcontext(self, record, value):  # text only
        return ' '.join(value[record.target_example.main_subtoken_indices[-1]:])

    def render_rcontext(self, record, value):
        h = record.target_example.main_subtoken_indices[-1]  # beginning of right context
        tokens = [format_html('<span title="{}"' + self._gohead(q, record.target_example, rhs=True) + '>{}</span>', q, x) for q, x in enumerate(value[h:], start=h + 1)]
        spans_to_link = other_p_tokens_in_sentence(record.target_example)
        for (i, j), anno in sorted(spans_to_link.items(), reverse=True):
            assert i - h < len(tokens)
            if i >= h:
                assert j - h <= len(tokens)
                tokens[i - h:j - h] = [anno.tokenhtml(offsets=True)]
        return mark_safe(' '.join(tokens))

    def render_role(self, value):
        return value.html

    def render_function(self, value):
        return value.html

    def value_construal(self, value):
        return value if value.role is None else {True: '=', False: '≠'}[value.role == value.function]

    def render_construal(self, value):
        special = value.special and value.special.strip()
        return mark_safe(f'<a href="{value.url}" class="{"misc-label" if special else "construal"}">{self.value_construal(value)}</a>')

    def value_note(self, value):
        return value.strip()

    def render_note(self, value):
        v = self.value_note(value)
        if v:
            return format_html('<span title="{}" style="cursor: help">ℹ</span>', v)
        else:
            return ''

    def value_sourcesentid(self, value):  # text only
        return value.sourcesentid

    def render_sourcesentid(self, value):
        return value.html

    def value_targetsentid(self, value):  # text only
        return value.targetsentid

    def render_targetsentid(self, value):
        return value.html

    class Meta:
        model = ParallelPTokenAlignment
        fields = (
        'target_example.adp_pos', 'target_example.gov_head', 'target_example.gov_pos', 'target_example.gov_supersense', 'target_example.obj_head', 'target_example.obj_pos', 'target_example.obj_supersense', 'target_example.gov_obj_syntax', 'target_example.is_transitive', 'target_example.is_typo', 'target_example.is_abbr')
        sequence = ('sourceexid','targetexid','sourcesentid','targetlanguage', 'lcontext', 'target', 'rcontext', 'role', 'construal', 'function', 'note')  # columns to prepose
        template_name = 'django_tables2/bootstrap.html'
        attrs = {'class': 'table ptokenannotation'}


def tokens_for_supersense(article_id):
    t = PTokenAnnotation.objects.select_related('construal__article__current_revision',
                                                'construal__role__article__current_revision', 'construal__function__article__current_revision',
                                                'usage__current_revision__metadatarevision__usagerevision__article_revision__article',
                                                'sentence', 'adposition').filter(Q(sentence__corpus__deprecated=False), Q(construal__role__article__id=article_id) | Q(construal__function__article__id=article_id)).order_by('sentence__sent_id')
    return t

def tokens_for_construal(article_id):
    t = PTokenAnnotation.objects.select_related('construal__article__current_revision',
        'construal__role__article__current_revision', 'construal__function__article__current_revision',
        'usage__current_revision__metadatarevision__usagerevision__article_revision__article',
        'sentence', 'adposition', 'sentence__corpus').filter(construal__article__id=article_id, sentence__corpus__deprecated=False).order_by('sentence__sent_id')
    return t

def tokens_for_adposition(article_id):
    t = PTokenAnnotation.objects.select_related('construal__article__current_revision',
        'construal__role__article__current_revision', 'construal__function__article__current_revision',
        'usage__current_revision__metadatarevision__usagerevision__article_revision__article',
        'sentence', 'adposition', 'sentence__corpus').filter(adposition__article__id=article_id, sentence__corpus__deprecated=False).order_by('sentence__sent_id')
    return t

def tokens_for_usage(article_id):
    t = PTokenAnnotation.objects.select_related('construal__article__current_revision',
        'construal__role__article__current_revision', 'construal__function__article__current_revision',
        'usage__current_revision__metadatarevision__usagerevision__article_revision__article',
        'sentence', 'adposition', 'sentence__corpus').filter(usage__article__id=article_id, sentence__corpus__deprecated=False).order_by('sentence__sent_id')
    return t

token_funcs = {
    'supersense': tokens_for_supersense,
    'construal': tokens_for_construal,
    'adposition': tokens_for_adposition,
    'usage': tokens_for_usage
}


def ptoken_data_table(request, metadata_type=None, article_id=None):
    try:
        t = token_funcs[metadata_type](article_id)
        if len(t) == 0:
            raise Http404(f"Couldn't find tokens for article {article_id} of type '{metadata_type}'")
    except KeyError:
        return HttpResponseBadRequest(f"Invalid metadata type: '{metadata_type}'")

    table = PTokenAnnotationTable(t)
    # check url query string for ?perpage=..., else default to 25
    per_page = request.GET.get("perpage", 25)
    RequestConfig(request, paginate={"per_page": per_page}).configure(table)
    return render(request, "ptoken_data_table.html", {"tokstable": table})


