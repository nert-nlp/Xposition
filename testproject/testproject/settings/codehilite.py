from __future__ import absolute_import, unicode_literals

from testproject.settings import *
from testproject.settings.local import *

# Test codehilite with pygments

WIKI_MARKDOWN_HTML_WHITELIST = ['a', 'abbr', 'acronym', 'b', 'blockquote', 
                                'code', 'em', 'i', 'li', 'ol', 'strong', 
                                'ul', 'figure', 'figcaption', 'br', 'hr', 
                                'p', 'div', 'img', 'pre', 'span', 'sub', 'sup', 
                                'table', 'thead', 'tbody', 'th', 'tr', 'td', 
                                'dl', 'dt', 'dd', 'h0', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'h7']

WIKI_MARKDOWN_KWARGS = {
    'extensions': [
        'codehilite',
        'footnotes',
        'attr_list',
        'headerid',
        'extra',
    ]}
