from xp.settings import *
from xp.settings.local import *

WIKI_MARKDOWN_HTML_WHITELIST = ['sub', 'sup', 'hr', 'u']

# Test codehilite with pygments

WIKI_MARKDOWN_KWARGS = {
    'extensions': [
        'codehilite',
        'footnotes',
        'attr_list',
        'headerid',
        'extra',
    ]}
