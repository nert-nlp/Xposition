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
Step 0) Put file streusle.go.notes.json in scripts directory.
     0a) Get the file streusle.json from github.com/nert-gu/streusle
     0b) Run govobj.py and annotator_notes.py to get streusle.go.notes.json
Step 1) Run it once to import `AdpositionRevision`s, `SupersenseRevision`s, and `CorpusSentence`s.
     1a) The file for `CorpusSentence`s must be converted to an Excel worksheet
Step 2) Run again for `Construal`s.
Step 3) Run againg for `UsageRevision`s.
Step 4) Run againg for `PTokenAnnotation`s
That way the script can access the ids for foreign keys: `Adposition`, `Supersense`, etc.