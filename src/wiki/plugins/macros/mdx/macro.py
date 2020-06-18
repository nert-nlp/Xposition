import re
import markdown
from markdown.util import etree
from django.template.loader import render_to_string
from django.utils.translation import gettext as _

from wiki.plugins.macros import settings
from wiki.plugins.metadata import models
from wiki.models import Article
from django.utils.html import escape, mark_safe, format_html

# See:
# http://stackoverflow.com/questions/430759/regex-for-managing-escaped-characters-for-items-like-string-literals
re_sq_short = r'"([^"\\]*(?:\\.[^"\\]*)*)"'

# can't compile: markdown.inlinepatterns.Pattern expects a string
MACRO_RE = r"(?i)(\[(?P<macro>\w+)(?P<kwargs>(\s(\w+:)?(%s|[\w'`&!%%+/$-]+))*)\])" % re_sq_short
MACRO_RE_COMPILED = re.compile(MACRO_RE)
KWARG_RE = re.compile(
    r'\s*((?P<arg>\w+):)?(?P<value>(%s|[^\s:]+))' %
    re_sq_short,
    re.IGNORECASE)

# Positional macros were deprecated in markdown 3.0, so we need to kwargize
# the existing positional macros during the preprocessing step. This dict
# determines what the keywords will be for the macros with positional
# invocations.
POSITIONAL_MACROS = ["p", "pspecial", "ss", "exref", "ex", "gex"]


class MacroExtension(markdown.Extension):
    """ Macro plugin markdown extension for django-wiki. """

    def extendMarkdown(self, md):
        md.preprocessors.register(SubstitutionPreprocessor(), 'escaper', 5)
        md.inlinePatterns.register(MacroPattern(MACRO_RE, md), 'dw-macros', 5)
        md.postprocessors.register(SubstitutionPostprocessor(), 'unescaper', 5)


# Escaping --------------------------------------------------------------------------------
ESCAPED = ["`"]


def escape_pattern(pattern):
    return "YyYeScApEYyY" + str(ord(pattern)) + "YyYEsCaPeYyY"


def escape_patterns_in_string(s):
    for pattern in ESCAPED:
        s = s.replace(pattern, escape_pattern(pattern))
    return s


class SubstitutionPreprocessor(markdown.preprocessors.Preprocessor):
    def run(self, lines):
        new_lines = []
        for line in lines:
            for pattern in ESCAPED:
                offset = 0
                for m in MACRO_RE_COMPILED.finditer(line):
                    span = m.group()
                    new_span = span.replace(pattern, escape_pattern(pattern))
                    line = line[:m.start() + offset] + new_span + line[m.end() + offset:]
                    offset += len(new_span) - len(span)
            new_lines.append(line)
        return new_lines


class SubstitutionPostprocessor(markdown.postprocessors.Postprocessor):
    def run(self, text):
        for pattern in ESCAPED:
            text = text.replace(escape_pattern(pattern), pattern)
        return text


# Macro implementation ----------------------------------------------------------------------
class MacroPattern(markdown.inlinepatterns.Pattern):
    """django-wiki macro preprocessor - parse text for various [some_macro] and
    [some_macro (kw:arg)*] references. """

    def handleMatch(self, m):
        macro = m.group('macro').strip()
        if macro not in settings.METHODS or not hasattr(self, macro):
            return m.group(2)

        kwargs = m.group('kwargs')
        if not kwargs:
            return getattr(self, macro)()
        kwargs_dict = {}
        for i, kwarg in enumerate(KWARG_RE.finditer(kwargs)):

            # Begin Xposition-specific hack: if there's no :, we have a positional macro
            arg = kwarg.group('arg')
            value = kwarg.group('value')
            if arg is None and macro in POSITIONAL_MACROS:
                arg = "arg" + str(i)
                if len(value) > 2 and value[0] == '"' and value[-1] == '"':
                    value = value[1:-1]
            elif arg is None:
                arg = value
                value = True
            if isinstance(value, str):
                # If value is enclosed with ': Remove and
                # remove escape sequences
                if value.startswith("'") and len(value) > 2:
                    value = value[1:-1]
                    value = value.replace("\\\\", "¤KEEPME¤")
                    value = value.replace("\\", "")
                    value = value.replace("¤KEEPME¤", "\\")
            kwargs_dict[str(arg)] = value
        return getattr(self, macro)(**kwargs_dict)

    def article_list(self, depth="2"):
        html = render_to_string(
            "wiki/plugins/macros/article_list.html",
            context={
                'article_children': self.markdown.article.get_children(
                    article__current_revision__deleted=False),
                'depth': int(depth) + 1,
            })
        return self.markdown.htmlStash.store(html)

    article_list.meta = dict(
        short_description=_('Article list'),
        help_text=_('Insert a list of articles in this level.'),
        example_code='[article_list depth:2]',
        args={'depth': _('Maximum depth to show levels for.')}
    )

    def toc(self):
        return "[TOC]"

    toc.meta = dict(
        short_description=_('Table of contents'),
        help_text=_('Insert a table of contents matching the headings.'),
        example_code='[TOC]',
        args={}
    )

    def wikilink(self):
        return ""

    wikilink.meta = dict(
        short_description=_('WikiLinks'),
        help_text=_(
            'Insert a link to another wiki page with a short notation.'),
        example_code='[[WikiLink]]',
        args={})

    def p(self, **kwargs):
        try:
            args = argize_kwargs(kwargs)
            cl = None
            prep = args[0]
            short = prep.split('/')[-1]
            p = models.Adposition.normalize_adp(cls=models.Adposition,
                                                adp=short,
                                                language_name=prep.split('/')[-2])
            if p:
                prep = prep.replace(short, p)
            if len(args) >= 3:
                cl = args[2]
            if len(args) > 1 and not '-' == args[1]:
                construal = args[1]
                if '`' in construal:
                    return link(short, '/' + prep + '/' + construal, cl if cl else 'usage')
                elif "'" in construal or '?' in construal:
                    return link(short.replace('--', '&#x219d;'), '/' + prep + '/' + construal, cl if cl else 'usage')
                else:
                    cl = cl if cl else 'usage'
                    if '--' in construal:  # 2 supersenses specified: role, function
                        ss1, ss2 = get_supersenses_for_construal(construal)
                        supersenses = (ss1, ss2)
                    else:
                        ss = get_supersense(construal)
                        if ss is None:  # special (backtick) labels are represented as construals with no role or function
                            supersenses = ()
                        else:  # single supersense specified, so it will be both role and function in the construal
                            supersenses = (ss,)
                            construal = construal + '--' + construal
                    cl += " usage-deprecated" if any(ss_is_deprecated(ss) for ss in supersenses) else ""
                    short = short.replace('--', '&#x219d;')
                    href = '/' + prep + '/' + construal
                    link_elt = etree.fromstring(f'<a class="{cl}" href="{href}"></a>')
                    link_elt.text = short
                    return link_elt
        except:
            span = '<span class="error">' + 'Macro Error: please see example usage' + '</span>'
            return etree.fromstring(span)
        return link(short, '/' + prep, cl if cl else 'adposition')

    # meta data
    p.meta = dict(
        short_description=_('Link to Adposition, Usage'),
        help_text=_('Create a link to a preposition or preposition-construal pair'),
        example_code='[p en/in] or [p en/in Locus--Locus]',
        args={'prep': _('Name of adposition'), 'construal': _('Name of construal'), 'class': _('optional class')}
    )

    def pspecial(self, **kwargs):
        try:
            args = argize_kwargs(kwargs)
            cl = None
            text = args[0]
            prep = args[1]
            p = models.Adposition.normalize_adp(cls=models.Adposition,
                                                adp=prep.split('/')[-1],
                                                language_name=prep.split('/')[-2])
            if p:
                prep = prep.replace(prep.split('/')[-1], p)
            if len(args) >= 4:
                cl = args[3]

            if len(args) > 2 and not '-' == args[2]:
                construal = args[2]
                if '`' in construal:
                    return link(text, '/' + prep + '/' + construal, cl if cl else 'usage')
                elif "'" in construal or '?' in construal:
                    return link(text.replace('--', '&#x219d;'), '/' + prep + '/' + construal, cl if cl else 'usage')
                else:
                    cl = cl if cl else 'usage'
                    if '--' in construal:  # 2 supersenses specified: role, function
                        ss1, ss2 = get_supersenses_for_construal(construal)
                        supersenses = (ss1, ss2)
                    else:
                        ss = get_supersense(construal)
                        if ss is None:  # special (backtick) labels are represented as construals with no role or function
                            supersenses = ()
                        else:  # single supersense specified, so it will be both role and function in the construal
                            supersenses = (ss,)
                            construal = construal + '--' + construal
                    cl += " usage-deprecated" if any(ss_is_deprecated(ss) for ss in supersenses) else ""
                    text = text.replace('--', '&#x219d;')
                    href = '/' + prep + '/' + construal
                    link_elt = etree.fromstring(f'<a class="{cl}" href="{href}"></a>')
                    link_elt.text = text
                    return link_elt
        except:
            span = '<span class="error">' + 'Macro Error: please see example usage' + '</span>'
            return etree.fromstring(span)
        return link(text, '/' + prep, cl if cl else 'adposition')

    # meta data
    pspecial.meta = dict(
        short_description=_('Link to Adposition, Usage'),
        help_text=_('Create a link to a preposition or preposition-construal pair with special (nonstandard) spelling or noncanonical capitalization'),
        example_code='[pspecial In en/in] or [pspecial In en/in Locus--Locus]',
        args={'prep': _('Name of adposition'), 'special': _('Text to display'), 'construal': _('Name of construal'), 'class': _('optional class')}
    )

    def ss(self, **kwargs):
        try:
            args = argize_kwargs(kwargs)

            cl = None
            if len(args) >= 2:
                cl = args[1]

            self_reference = args[0] == escape_patterns_in_string(self.markdown.article.current_revision.title)

            if '--' in args[0]:
                ss1, ss2 = get_supersenses_for_construal(args[0])
                cls = cl or 'construal'
                if self_reference:
                    cls += " this-construal"
                    cspan = construal_span(ss1, ss2, cls)
                    return cspan
                else:
                    clink = construal_link(ss1, ss2, '/' + args[0], cl if cl else 'construal')
                    return clink
            else:
                supersense = get_supersense(args[0])
                display = args[0].replace('`', r'\`')
                cls = cl or 'supersense'
                if args[0] in ['??', '`d', '`i', '`c', '`$']:
                    cls = cl or 'misc-label'
                if self_reference:
                    span = etree.Element("span")
                    span.set("class", cls + " this-supersense")
                    span.text = display
                    return show_deprecation(supersense, span)
                link_elt = link(display, '/' + args[0].replace('`', '%60'), cls)
                return show_deprecation(supersense, link_elt)
        except:
            span = '<span class="error">' + 'Macro Error: please see example usage' + '</span>'
            return etree.fromstring(span)

    # meta data
    ss.meta = dict(
        short_description=_('Link to Supersense or Construal'),
        help_text=_('Create a link to a supersense or construal'),
        example_code='[ss Locus] or [ss Locus--Locus]',
        args={'name': _('Name of supersense/construal label'), 'class': _('optional class')}
    )

    def exref(self, **kwargs):
        try:
            args = argize_kwargs(kwargs)
            id = args[0]
            page = args[1]
            my_title = escape_patterns_in_string(self.markdown.article.current_revision.title)
            ref_title = page
            ref_slug = page
            # try to find article
            x = Article.objects.filter(current_revision__title=ref_title)
            # check for article with matching title
            if x:
                ref_slug = str(x[0].urlpath_set.all()[0])
                if ref_slug[0] == '/':
                    ref_slug = ref_slug[1:]
                if ref_slug[-1] == '/':
                    ref_slug = ref_slug[:-1]

            supersense = get_supersense(args[1])

            a = etree.Element("a")
            a.set("href", '/' + ref_slug + '/#' + id)
            a.set("class", 'exref')
            if supersense is not None and ref_title != my_title:
                ss_span = etree.SubElement(a, 'span')
                ss_span.text = ref_title
                ss_span = show_deprecation(supersense, ss_span, normal_class="", deprecated_class="exref-deprecated")
                rest_span = etree.SubElement(a, 'span')
                rest_span.text = f'#{id}'
            else:
                display = f'{ref_title}#{id}' if not ref_title == my_title else f'#{id}'
                a.text = display
        except:
            span = '<span class="error">' + 'Macro Error: please see example usage' + '</span>'
            return etree.fromstring(span)
        return a

    # meta data
    exref.meta = dict(
        short_description=_('Link to Example'),
        help_text=_('Create a link to an example sentence'),
        example_code='[exref 001 Locus]',
        args={'id': _('id of example'), 'page': _('title of page example is on')}
    )

    def ex(self, **kwargs):
        try:
            args = argize_kwargs(kwargs)
            id = args[0]
            sent = args[1]
            label = args[2] if len(args) > 2 else None

            span = etree.Element("span")
            span.set("id", id)
            span.set("class", "example")
            sent_span = etree.SubElement(span, "span")
            sent_span.text = sent + " "

            if label:
                exlabel_span = etree.SubElement(span, "span")
                exlabel_span.set("class", "exlabel")
                exlabel_span.text = label
            else:
                exlabel_a = etree.SubElement(span, "a")
                exlabel_a.set("class", "exlabel")
                exlabel_a.set("href", "#" + id)
                exlabel_a.text = id
        except:
            span = '<span class="error">' + 'Macro Error: please see example usage' + '</span>'
            return etree.fromstring(span)
        return span

    # meta data
    ex.meta = dict(
        short_description=_('Create an Example'),
        help_text=_('Create an example sentence with a linkable id'),
        example_code='[ex 001 "The cat [p en/under Locus] the table."]',
        args={'id': _('id of example'), 'sent': _('full sentence in double quotes'), 'label': _('string to display after ex. (if not id)')}
    )

    GLOSS_RE = re.compile('^\{(?P<tok_gloss>[^}]*?)\}')

    def gex(self, **kwargs):
        try:
            args = argize_kwargs(kwargs)
            id = args[0]
            sent = args[1]
            sent_gloss = args[2] if len(args) > 2 else ''
            columns = []
            while len(sent) > 0:
                gloss = self.GLOSS_RE.match(sent)
                if gloss:
                    word_gloss = gloss.group('tok_gloss')
                    sent = sent[len(gloss.group()):]
                    if '||' in word_gloss:
                        xs = word_gloss.split('||')
                    else:
                        xs = word_gloss.split()
                    xs = [escape(x) for x in xs]
                    column = etree.Element("div")
                    column.set("class", "gll")
                    for i, x in enumerate(xs):
                        span_x = etree.SubElement(column, "span")
                        if i != len(xs) - 1:
                            etree.SubElement(span_x, "br")
                        span_x.text = x
                else:
                    end = sent.index('{') if '{' in sent else len(sent)
                    word_gloss = sent[:end]
                    sent = sent[len(word_gloss):]
                    if word_gloss.strip():
                        column = etree.Element("div")
                        column.set("class", "gll")
                        column.text = word_gloss.strip()
                    else:
                        column = etree.Element("span")
                columns.append(column)

            span = etree.Element("span")
            span.set("id", id)
            span.set("class", "example")
            div = etree.SubElement(span, "div")
            div.set("class", "interlinear example")
            p_interlinear = etree.SubElement(div, "p")
            p_interlinear.set("class", "gloss")
            for col in columns:
                p_interlinear.append(col)
            p_trans = etree.SubElement(div, "p")
            p_trans.set("class", "translation")
            span_trans = etree.SubElement(p_trans, "span")
            span_trans.text = "'" + sent_gloss + "' "
            a_ex = etree.SubElement(p_trans, "a")
            a_ex.set("href", "#" + id)
            a_ex.set("class", "exlabel")
            a_ex.text = id
        except:
            span = '<span class="error">'+'Macro Error: please see example usage'+'</span>'
            return etree.fromstring(span)
        return span

    # meta data
    gex.meta = dict(
        short_description=_('Create a Glossed Example'),
        help_text=_('Create an example sentence word and sentence translation displayed on separate lines.'),
        example_code='[gex 001 '
                     '"{L\' the}{éléphant elephant} {gris gray} est<br> {[p fr/dans Locus]||[p en/in Locus]} {la voiture||the car}." '
                     '"The gray elephant is in the car."]',
        args={'id': _('id of example'),
              'sent': _('full sentence in double quotes with glossed tokens as {token||gloss}'),
              'sent_gloss': _('glossed translation of sentence'),
              'label': _('string to display after ex. (if not id)')}
    )


def link(t, l, clazz):
    a = etree.Element("a")
    a.set("href", l)
    a.set("class", clazz)
    a.text = t
    return a


def makeExtension(*args, **kwargs):
    """Return an instance of the extension."""
    return MacroExtension(*args, **kwargs)


def argize_kwargs(kwargs):
    args = []
    # arg0, arg1, ..., arg10, etc.
    for arg in sorted(kwargs.keys(), key=lambda x: int(x[3:])):
        args.append(kwargs[arg])
    return args


def ss_is_deprecated(ss):
    return ss is None or ss.current_revision.metadatarevision.supersenserevision.deprecated


def show_deprecation(ss, elt, normal_class="supersense", deprecated_class="supersense-deprecated"):
    # unclear why `entry.deprecated` didn't work..
    if ss is not None and ss_is_deprecated(ss):
        elt.set("class", normal_class + " " + deprecated_class)
    return elt


def get_supersense(supersense_string):
    try:
        return models.Supersense.objects.get(category__name=supersense_string)
    except models.Supersense.DoesNotExist:
        return None


def get_supersenses_for_construal(construal_string):
    try:
        ss_name_1, ss_name_2 = construal_string.split('--')
    except ValueError:
        ss1, ss2 = None, None
    else:
        ss1 = get_supersense(ss_name_1)
        ss2 = get_supersense(ss_name_2)

    return ss1, ss2


def construal_span(ss1, ss2, cls):
    span1 = '<span' + (' class="supersense-deprecated">' if ss_is_deprecated(ss1) else '>')
    span1 += ss1.current_revision.metadatarevision.name if ss1 else 'INVALIDSS'
    span1 += '</span>'
    span2 = '<span' + (' class="supersense-deprecated">' if ss_is_deprecated(ss2) else '>')
    span2 += ss2.current_revision.metadatarevision.name if ss2 else 'INVALIDSS'
    span2 += '</span>'
    span = f'<span class="{cls}">{span1}&#x219d;{span2}</span>'
    return etree.fromstring(span)


def construal_link(ss1, ss2, href, cls):
    span1 = '<span' + (' class="supersense-deprecated">' if ss_is_deprecated(ss1) else '>')
    span1 += ss1.current_revision.metadatarevision.name if ss1 else 'INVALIDSS'
    span1 += '</span>'
    span2 = '<span' + (' class="supersense-deprecated">' if ss_is_deprecated(ss2) else '>')
    span2 += ss2.current_revision.metadatarevision.name if ss2 else 'INVALIDSS'
    span2 += '</span>'
    a = f'<a href="{href}" class="{cls}">{span1}&#x219d;{span2}</a>'
    return etree.fromstring(a)
