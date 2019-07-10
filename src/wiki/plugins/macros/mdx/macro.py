import re

import markdown
from django.template.loader import render_to_string
from django.utils.translation import gettext as _
from wiki.plugins.macros import settings
from wiki.plugins.metadata import models

# See:
# http://stackoverflow.com/questions/430759/regex-for-managing-escaped-characters-for-items-like-string-literals
re_sq_short = r"'([^'\\]*(?:\\.[^'\\]*)*)'"

MACRO_RE = r"((?i)\[(?P<macro>\w+)(?P<kwargs>\s\w+\:.+)*\])"
KWARG_RE = re.compile(
    r'\s*(?P<arg>\w+)(:(?P<value>([^\']+|%s)))?' %
    re_sq_short,
    re.IGNORECASE)


class MacroExtension(markdown.Extension):
    """ Macro plugin markdown extension for django-wiki. """

    def extendMarkdown(self, md):
        md.inlinePatterns.add('dw-macros', MacroPattern(MACRO_RE, md), '>link')


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
        for kwarg in KWARG_RE.finditer(kwargs):
            arg = kwarg.group('arg')
            value = kwarg.group('value')
            if value is None:
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

    def p(self, *args):
        cl = None
        prep = args[0]
        short = prep.split('/')[-1]
        prep = prep.replace(short, models.Adposition.normalize_adp(short, prep.split('/')[-2]))
        if len(args) >= 3:
            cl = args[2]
        if len(args) > 1 and not '-' == args[1]:
            construal = args[1]
            if '`' in construal:
                return link(short, '/' + prep + '/' + construal.replace('`', "'"), cl if cl else 'usage')
            elif '--' in construal:
                return link(short.replace('--','&#x219d;'), '/' + prep + '/' + construal, cl if cl else 'usage')
            else:
                return link(short, '/' + prep + '/' + construal + '--' + construal, cl if cl else 'usage')
        return link(short, '/' + prep, cl if cl else 'adposition')
    # meta data
    p.meta = dict(
        short_description=_('Link to Adposition, Usage'),
        help_text=_('Create a link to a preposition or preposition-construal pair'),
        example_code='[p en/in] or [p en/in Locus--Locus]',
        args={'prep': _('Name of adposition'), 'construal': _('Name of construal'), 'class': _('optional class')}
    )

    def pspecial(self, *args):
        cl = None
        prep = args[0]
        short = prep.split('/')[-1]
        prep = prep.replace(short, models.Adposition.normalize_adp(short, prep.split('/')[-2]))
        short = args[1]
        if len(args) >= 4:
            cl = args[3]
        if len(args) > 2 and not '-' == args[2]:
            construal = args[2]
            if '`' in construal:
                return link(short, '/' + prep + '/' + construal.replace('`', "'"), cl if cl else 'usage')
            elif '--' in construal:
                return link(short.replace('--', '&#x219d;'), '/' + prep + '/' + construal, cl if cl else 'usage')
            else:
                return link(short, '/' + prep + '/' + construal + '--' + construal, cl if cl else 'usage')
        return link(short, '/' + prep, cl if cl else 'adposition')
    # meta data
    pspecial.meta = dict(
        short_description=_('Link to Adposition, Usage'),
        help_text=_('Create a link to a preposition or preposition-construal pair with special (nonstandard) spelling'),
        example_code='[p en/in] or [p en/in Locus--Locus]',
        args={'prep': _('Name of adposition'), 'special': _('Text to display'), 'construal': _('Name of construal'), 'class': _('optional class')}
    )



    def ss(self, *args):
        cl = None
        if len(args) >= 2:
            cl = args[1]
        if "'" in args[0]:
            return link(args[0], '/' + args[0].replace("'", "`"), cl if cl else 'misc')
        elif '--' in args[0]:
            return link(args[0].replace('--','&#x219d;'), '/' + args[0], cl if cl else 'construal')
        else:
            return link(args[0], '/' + args[0], cl if cl else 'supersense')
    # meta data
    ss.meta = dict(
        short_description=_('Link to Supersense or Construal'),
        help_text=_('Create a link to a supersense or construal'),
        example_code='[ss Locus] or [ss Locus--Locus]',
        args={'name': _('Name of supersense/construal label'), 'class': _('optional class')}
    )

    def exref(self, id, page):
        return link('ex. ' + page + ' ' + id, '/' + page.replace('`', "'") + '/#' + id, 'exref')

    # meta data
    exref.meta = dict(
        short_description=_('Link to Example'),
        help_text=_('Create a link to an example sentence'),
        example_code='[exref 001 Locus]',
        args={'id': _('id of example'), 'page': _('page example is on')}
    )

    def ex(self, id, sent, label=None):
        return '<a id="' + id + '"></a>"<span class="example">' + sent + '</span>" (' + (label if label else id) + ')'
    # meta data
    ex.meta = dict(
        short_description=_('Create an Example'),
        help_text=_('Create an example sentence with a linkable id'),
        example_code='[ex 001 \'The cat [p en/under Locus] the table.\']',
        args={'id': _('id of example'), 'sent': _('full sentence in single quotes'), 'label': _('string to display after ex. (if not id)')}
    )


def link(t, l, clazz):
    return '<a href="' + l + '" class="' + clazz + '">' + t + '</a>'

def makeExtension(*args, **kwargs):
    """Return an instance of the extension."""
    return MacroExtension(*args, **kwargs)
