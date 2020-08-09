# Xposition

__Xposition__ (URL forthcoming) is a multilingual database of the semantics of adpositions (prepositions, postpositions) and case markers.
Semantic information is primarily categorized in terms of coarse-grained __supersenses__.
The database is designed to support corpus annotation.

Xposition is the successor to [PrepWiki](http://demo.ark.cs.cmu.edu/PrepWiki/), which was limited to English prepositions
and used an earlier inventory of supersenses.

## Languages

Initial languages:

* English
* Hebrew (Modern)
* Hindi
* Korean

If you would like to contribute to these or other languages, let us know.


# Installation

Note: Xposition requires Python 3.6+. 

0. We recommend you [create a new conda environment](https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html#creating-an-environment-with-commands) for Xposition:

```sh
conda create --name Xposition python=3.7
conda activate Xposition
```

1. Once you've cloned the git repository, you'll need to install the __django-wiki__ and __django-categories__ libraries (and their dependencies):

```sh
git clone git@github.com:nert-nlp/Xposition.git --recursive
cd Xposition
pip install -r requirements.txt
# make sure submodules were cloned
git submodule update
```

## Configuration

1. Create the file `xposition/xp/settings/unversioned.py`, which
contains a variable `SECRET_KEY`. Do not commit this file to git.

```sh
echo 'SECRET_KEY = "..."' > xposition/xp/settings/unversioned.py
```

2a. If you are configuring Xposition for **development**, make sure that the end
of `xposition/xp/settings/local.py` has the `.dev` import
**uncommented**, and the `.base` import commented, like this:

```py
from .dev import *
#from .base import *
```

2b. If you are configuring Xposition for **production**, make sure that the end
of `xposition/xp/settings/local.py` has the `.base` import
**uncommented**, and the `.dev` import commented, like this:

```py
#from .dev import *
from .base import *
```

3. Run the migration to update the server's SQL schema:

```sh
python xposition/manage.py migrate 
```

## Running
You should now be able to run the server:

```sh
python xposition/manage.py runserver
```

**Note**: If you are running on Windows, you might get an error about `wiki.plugins.categories`. This is because a Unix symlink is not interpreted propertly by Windows. In the `xposition` directory, remove `wiki` and replace it with a Windows symlink: `mklink /D wiki ..\src\wiki`.

## Login

Django admin:

  * Username: `admin`
  * Password: `admin`

## Testing

This project can be run directly with the manage.py script, provided
that you have checked out the root of the Git repository.

It comes with a prepopulated SQLite database.

## Importing a new Corpus

We use the library django-import-export for loading new models when there are too many to create by hand. Developers can follow the following procedure to load a new corpus into the database.

- On the homepage, click the language you are working with and then click metadata (You may first need to create the Language object if it doesn't exist. In this case, click metadata on the homepage). Click `Create a Corpus` and fill out the form.
- The corpus you want to import must be in the STREUSLE json format. Place it in the directory `<Xposition>/scripts`.
- Modify the top of the file `new_corpus.py` so that the constants `LANGUAGE`, `CORPUS`, etc. are correct.
- Go to the xposition directory: `cd <Xposition>\xposition`
- Import new supersenses and adpositions:
	- Run `python manage.py shell` and then type `exec(open(r'..\scripts\generate_basic_files.py').read())`. This will create json files for all supersenses and adpositions in the corpus and it will place them in `<Xposition>/scripts/<corpus><version>_files`. 
	- You can then import new supersenses and adpositions through the admin interface on the webpage at `<homepage_url>/admin`, by clicking `Supersense revisions` or `Adposition revisions`, Import, and then choose the corresponding file from `<Xposition>/scripts/<corpus><version>_files`.
- Import new construals:
	- Run `python manage.py shell` and then type `exec(open(r'..\scripts\generate_construal_file.py').read())`. This will create a json file for all construals in the corpus. 
	- You can then import new construals through the admin interface on the webpage at `<homepage_url>/admin`, by clicking `Construals`, Import, and then choose the corresponding file from `<Xposition>/scripts/<corpus><version>_files`.
	- Note: Construals depend on supersenses, so if there are any supersenses missing from the database, you may get a 'Missing Supersense' error.
- Import new usages:
	- Run `python manage.py shell` and then type `exec(open(r'..\scripts\generate_usage_file.py').read())`. This will create a json file for all usages in the corpus. 
	- You can then import new usages through the admin interface on the webpage at `<homepage_url>/admin`, by clicking `Usage revisions`, Import, and then choose the corresponding file from `<Xposition>/scripts/<corpus><version>_files`.
	- Note: Usages depend on construals and adpositions, so if there are any construals or adpositions missing from the database, you may get a 'Missing' error.
- Import new sentences and ptoken_annotations:
	- Run `python manage.py shell` and then type `exec(open(r'..\scripts\generate_corpus_files.py').read())`. This will create tsv files for all CorpusSentences and PTokenAnnotations in the corpus. 
	- You can then import them through the admin interface on the webpage at `<homepage_url>/admin`, by clicking `Corpus sentences` or `Adposition token annotations`, Import, and then choose the corresponding file from `<Xposition>/scripts/<corpus><version>_files`. Adposition token annotations will be divided into multiple files labelled `ptoken_annotations0.tsv`, `ptoken_annotations1.tsv`, etc.  
	- Note: PTokenAnnotations depend on usages and adpositions, so if there are any usages or adpositions missing from the database, you may get a 'Missing' error.


# Credits

* Project leader: [Nathan Schneider](http://nathan.cl) (Georgetown)
* Xposition software development: Max Kim, Joseph Ledford (Georgetown)
* Other collaborators/contributors: TODO/see PrepWiki
