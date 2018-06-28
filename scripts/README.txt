convert_construal.py - creates construal articles (with our custom macros) from markdown_final folder
convert_finalversion - adds custom macros to markdown supersense articles
convert_tex2markdown - converts latex to markdown
import_corpus - import tsv style data into django as CorpusSentence and PTokenAnnotation objects
json2django_models - creates tsv files from json corpus data
------------------------------------------------------------------
To use json2django_models.py,
```
cd <Xposition>\testproject
python manage.py shell
import json
exec(open(r'..\scripts\json2django_models.py').read())
```
You can run it once to import `AdpositionRevision`s, `SupersenseRevision`s, `UsageRevision`s and `Construal`s.
You should run it a second time before you import `CorpusSentence`s and `PTokenAnnotation`s. That way the script can 
access the `Adposition`, `Supersense`, etc. ids.