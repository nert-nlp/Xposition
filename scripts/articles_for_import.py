import re, os, django, json
os.chdir('..\scripts')

from collections import defaultdict
from wiki.plugins.metadata import models as ms

macro_dir = 'markdown-and-macros'
construal_dir = 'markdown-construals'
json_dir = 'json'

OUTPUT_SS_DESCRIPTIONS = False

def write_json(dir, output):
    ids = defaultdict(int)
    ids.setdefault(0)
    for a in ms.Article.objects.all():
        ids[str(a.urlpath_set.all()[0])[:-1]] = a.pk
    # print(ids)

    articles = []
    short_descriptions = []

    for file in os.listdir(dir):
        if file.endswith('.txt'):
            text = open(os.path.join(dir, file), 'r', encoding='utf8').read()
            SHORT_RE = re.compile('<short_description>(?P<desc>.+?)</short_description>', re.DOTALL)
            content = SHORT_RE.sub('', text)
            short = SHORT_RE.search(text).group() if SHORT_RE.search(text) else ''

            articles.append(
                {'content':content,
                 'title':file.replace('.txt',''),
                 'article_id':str(ids[file.replace('.txt','')])}
            )
            if short:
                # print(short)
                short_descriptions.append('\n'+short)

    with open(output, 'w', encoding='utf8') as f:
        json.dump(articles,f)
    if short_descriptions and OUTPUT_SS_DESCRIPTIONS:
        with open('ss_short_descriptions.txt', 'w', encoding='utf8') as f:
            f.write('\n\n'.join(short_descriptions))


if not os.path.exists(json_dir):
    os.makedirs(json_dir)
outfile = os.path.join(json_dir,'supersense_article_revisions.json')
write_json(macro_dir,outfile)
if os.path.exists(construal_dir):
    outfile = os.path.join(json_dir, 'construal_article_revisions.json')
    write_json(construal_dir, outfile)
misc_dir = os.path.join(macro_dir,'misc')
if os.path.exists(misc_dir):
    outfile = os.path.join(json_dir, 'misc_article_revisions.json')
    write_json(misc_dir, outfile)