# -*- coding: utf-8 -*-


from __future__ import absolute_import, unicode_literals
import re
import markdown
from django.template.loader import render_to_string
from django.utils.translation import ugettext as _
from six import string_types
from wiki.plugins.macros import settings

# See:
# http://stackoverflow.com/questions/430759/regex-for-managing-escaped-characters-for-items-like-string-literals
re_sq_short = r"'([^'\\]*(?:\\.[^'\\]*)*)'"

MACRO_RE = re.compile(
    r"(\[(?P<macro>\w+?)(?P<args>(\s(\S+?(%s)?))*?)\])",

    re.IGNORECASE | re.UNICODE)

ARG_RE = re.compile(
    r"\s(\w+:)?(?P<value>(%s|[^\s:]+))" %
    re_sq_short,
    re.IGNORECASE | re.UNICODE)


class MacroExtension(markdown.Extension):
    """ Macro plugin markdown extension for django-wiki. """

    def extendMarkdown(self, md, md_globals):
        """ Insert MacroPreprocessor before ReferencePreprocessor. """
        md.preprocessors.add('dw-macros', MacroPreprocessor(md), '>html_block')


class MacroPreprocessor(markdown.preprocessors.Preprocessor):
    """django-wiki macro preprocessor - parse text for various [some_macro] and
    [some_macro (kw:arg)*] references. """

    def run(self, lines):
        # Look at all those indentations.
        # That's insane, let's get a helper library
        # Please note that this pattern is also in plugins.images
        new_text = []
        for line in lines:
            for m in MACRO_RE.finditer(line):
                macro = m.group('macro').strip()
                for test_macro in settings.METHODS:
                    if macro == test_macro and hasattr(self, macro):
                        args = m.group('args')
                        if args:
                            args_list = []
                            for arg in ARG_RE.finditer(args):
                                value = arg.group('value')
                                # if value is None:
                                # value = True
                                if isinstance(value, string_types):
                                    # If value is enclosed with ': Remove and
                                    # remove escape sequences
                                    if value.startswith("'") and len(value) > 2:
                                        value = value[1:-1]
                                        value = value.replace("\\\\", "¤KEEPME¤")
                                        value = value.replace("\\", "")
                                        value = value.replace("¤KEEPME¤", "\\")
                                if value is not None:
                                    args_list.append(value)
                            line = line[:m.start()] + getattr(self, macro)(*args_list) + line[m.end():]
                        else:
                            line = line[:m.start()] + getattr(self, macro)() + line[m.end():]
            if line is not None:
                new_text.append(line)
        return new_text

    def article_list(self, depth="2"):
        html = render_to_string(
            "wiki/plugins/macros/article_list.html",
            context={
                'article_children': self.markdown.article.get_children(
                    article__current_revision__deleted=False),
                'depth': int(depth) + 1,
            })
        return self.markdown.htmlStash.store(html, safe=True)
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
        if len(args) >= 3:
            cl = args[2]
        if len(args) > 1 and not '-' == args[1]:
            prep, construal = args[0], args[1]
            short = prep.split('/')[-1]
            if '`' in args[0]:
                return link(short, '/' + prep + '/' + construal.replace('`', "'"), cl if cl else 'usage')
            elif '--' in args[0]:
                return link(short, '/' + prep + '/' + construal, cl if cl else 'usage')
            else:
                return link(short, '/' + prep + '/' + construal + '--' + construal, cl if cl else 'usage')
        return link(args[0].split('/')[-1], '/' + args[0], cl if cl else 'adposition')
    # meta data
    p.meta = dict(
        short_description=_('Link to Adposition, Usage'),
        help_text=_('Create a link to a preposition or preposition-construal pair'),
        example_code='[p en/in] or [p en/in Locus--Locus]',
        args={'prep': _('Name of adposition'), 'construal': _('Name of construal'), 'class': _('optional class')}
    )


    def ss(self, *args):
        cl = None
        if len(args) >= 2:
            cl = args[1]
        if '`' in args[0]:
            return link(args[0], '/' + args[0].replace('`', "'"), cl if cl else 'misc')
        elif '--' in args[0]:
            return link(args[0], '/' + args[0], cl if cl else 'construal')
        else:
            return link(args[0], '/' + args[0], cl if cl else 'supersense')
    # meta data
    ss.meta = dict(
        short_description=_('Link to Supersense or Construal'),
        help_text=_('Create a link to a supersense or construal'),
        example_code='[ss Locus] or [ss Locus--Locus]',
        args={'name': _('Name of supersense/construal label'), 'class': _('optional class')}
    )

	
def link(t, l, clazz):
    return '<a href="'+l+'" class="'+clazz+'">'+t+'</a>'