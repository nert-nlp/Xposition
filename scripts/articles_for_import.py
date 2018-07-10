import re, os, django, json
os.chdir('..\scripts')

from collections import defaultdict
from wiki.plugins.metadata import models as ms

dir = 'markdown-and-macros'
dir2 = 'markdown-construals'


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
            content = text.split('|')[-1]
            short = text.split('|')[-2] if len(text.split('|'))>1 else ''

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
    if short_descriptions:
        with open('ss_short_descriptions.txt', 'w', encoding='utf8') as f:
            f.write('\n\n'.join(short_descriptions))

write_json(dir,'supersense_article_revisions.json')
write_json(dir2, 'construal_article_revisions.json')