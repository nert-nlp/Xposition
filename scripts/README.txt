convert_construal.py - creates construal articles (with our custom macros) from markdown_final folder
convert_finalversion.py - adds custom macros to markdown supersense articles
convert_tex2markdown.py - converts latex to markdown
models_for_import.py - creates tsv files from json corpus data
articles_for_import.py - creates json for uploading articles (through the admin articlerevision interface)
------------------------------------------------------------------
To use models_for_import.py,
```
cd <Xposition>\testproject
python manage.py shell
exec(open(r'..\scripts\models_for_import.py').read())
```
Step 0) Put file streusle.go.notes.json in scripts directory.
     0a) Get the file streusle.json from github.com/nert-gu/streusle
     0b) Run govobj.py and annotator_notes.py to get streusle.go.notes.json
Step 1) Run the script once and then import `AdpositionRevision`s, `SupersenseRevision`s, and `CorpusSentence`s from admin.
        (the files for `CorpusSentence` and `PTokenAnnotation` must be converted to an Excel worksheet)
     1b) Create articles "English", "at", "Locus", "Locus--Locus", and "at: Locus--Locus" by hand.
Step 2) Run again and then import `Construal`s (depends on `SupersenseRevision`) from admin.
Step 3) Run again and then import `UsageRevision`s (depends on `Construal`) from admin.
Step 4) Run again and then import `PTokenAnnotation`s (depends on `UsageRevision`) from admin.
That way the script can access the ids for foreign keys: `Adposition`, `Supersense`, etc.