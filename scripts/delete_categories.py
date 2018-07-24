import re, os, django, json
os.chdir('..\scripts')

from wiki.plugins.metadata import models as ms
from wiki.plugins.categories.models import ArticleCategory

for adp in ms.Adposition.objects.all():
    cats = ArticleCategory.objects.filter(name=str(adp))
    if cats:
        print(cats)
        cats.delete()
for c in ms.Construal.objects.all():
    cats = ArticleCategory.objects.filter(name=str(c).replace(' ~> ', '--'))
    if cats:
        print(cats)
        cats.delete()


