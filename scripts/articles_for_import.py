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

    for file in os.listdir(dir):
        if file.endswith('.txt'):
            content = open(os.path.join(dir, file), 'r', encoding='utf8').read()
            content = content.split('|')[-1]

            articles.append(
                {'content':content,
                 'title':file.replace('.txt',''),
                 'article_id':str(ids[file.replace('.txt','')])}
            )

    with open(output, 'w', encoding='utf8') as f:
        json.dump(articles,f)

write_json(dir,'supersense_article_revisions.json')
write_json(dir2, 'construal_article_revisions.json')