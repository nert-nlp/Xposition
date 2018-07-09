from django.utils.html import conditional_escape, format_html, mark_safe
import django_tables2 as tables
from .models import PTokenAnnotation

def other_p_tokens_in_sentence(pt):
    others = pt.sentence.ptokenannotation_set.exclude(pk=pt.pk)
    result = {}
    for opt in others:
        assert opt.main_subtoken_indices[0] not in result
        assert opt.main_subtoken_indices[-1] not in result
        result[opt.main_subtoken_indices[0]-1,opt.main_subtoken_indices[-1]] = opt # open the link
    return result

class PTokenAnnotationTable(tables.Table):
    exid = tables.Column(accessor='id')
    lcontext = tables.Column(accessor='sentence.tokens', verbose_name='')
    target = tables.Column(accessor='sentence.tokens', verbose_name='P', order_by=('adposition', 'construal'))
    rcontext = tables.Column(accessor='sentence.tokens', verbose_name='')
    role = tables.Column(accessor='construal.role', verbose_name='Role')
    construal = tables.Column(accessor='construal', verbose_name='↝')
    function = tables.Column(accessor='construal.function', verbose_name='Function')
    note = tables.Column(accessor='annotator_cluster', verbose_name='ℹ')
    sentid = tables.Column(accessor='sentence', verbose_name='Sent ID')
    
    def render_exid(self, value):
        displaynum = value+3000    # TODO: link
        return format_html('<a href="/ex/{}" class="exnum">({})</a>', displaynum, displaynum)
    
    def value_lcontext(self, record, value):    # text only
        return ' '.join(value[:record.main_subtoken_indices[0]-1])

    def _gohead(self, i, pt):
        s = ''
        if i==pt.gov_head_index:
            s += 'govhead '
        if i==pt.obj_head_index:
            s += 'objhead '
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
                exnum = anno.id+3000
                displaystr = ' '.join(tokens[i:j])
                tokens[i:j] = [format_html('<a href="/ex/{}" class="exnum">', exnum) + displaystr + '</a>']
        return mark_safe(' '.join(tokens))

    def value_target(self, record, value):
        tokens = value[record.main_subtoken_indices[0]-1:record.main_subtoken_indices[-1]]
        return ' '.join(tokens)

    def render_target(self, record, value):
        tokens = [format_html('<span title="{}">{}</span>', i+1, value[i]) for i in range(record.main_subtoken_indices[0]-1, record.main_subtoken_indices[-1])]
        return mark_safe(format_html('<a href="{}" class="usage">', record.usage.current_revision.plugin.article.get_absolute_url()) + ' '.join(tokens) + '</a>')
    
    def value_rcontext(self, record, value):   # text only
        return ' '.join(value[record.main_subtoken_indices[-1]:])
    
    def render_rcontext(self, record, value):
        h = record.main_subtoken_indices[-1]    # beginning of right context
        tokens = [format_html('<span title="{}"' + self._gohead(q,record) + '>{}</span>', q, x) for q,x in enumerate(value[h:], start=h+1)]
        spans_to_link = other_p_tokens_in_sentence(record)
        for (i,j),anno in sorted(spans_to_link.items(), reverse=True):
            assert i-h<len(tokens)
            if i>=h:
                assert j-h<=len(tokens)
                exnum = anno.id+3000
                displaystr = ' '.join(tokens[i-h:j-h])
                tokens[i-h:j-h] = [format_html('<a href="/ex/{}" class="exnum">', exnum) + displaystr + '</a>']
        return mark_safe(' '.join(tokens))
    
    def render_role(self, value):
        return value.html()
        
    def render_function(self, value):
        return value.html()
    
    def value_construal(self, value):
        return value if value.role is None else {True: '=', False: '≠'}[value.role==value.function]
        
    def render_construal(self, value):
        return format_html('<a href="{}" class="construal">{}</a>', value.article.get_absolute_url(), self.value_construal(value))
    
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
        sentid = self.value_sentid(value)
        return format_html('<a href="{}/{}" class="corpussentence">{}</a>', value.corpus.article.get_absolute_url(), sentid, sentid)

    class Meta:
        model = PTokenAnnotation
        #fields = ('id', 'adposition', 'construal', 'usage', 'sentence')
        fields = ('adp_pos', 'gov_head', 'gov_pos', 'gov_supersense', 'obj_head', 'obj_pos', 'obj_supersense', 'gov_obj_syntax', 'is_transitive')
        sequence = ('exid', 'lcontext', 'target', 'rcontext', 'role', 'construal', 'function', 'note') # columns to prepose
        template_name = 'django_tables2/bootstrap.html'
        attrs = {'class': 'table ptokenannotation'}
