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

**Note**: If you are running on Windows, you might get an error about `wiki.plugins.categories`. This is because a Unix symlink is not interpreted propertly by Windows. In the `xposition` directory, remove `wiki` and replace it with a Windows symlink: `mklink /D wiki ..\src\wiki` as well as `mklink /D categories nert-nlp-django-categories\categories` in `Xposition\src\wiki\plugins`

## Login

Django admin:

  * Username: `admin`
  * Password: `admin`

## Testing

This project can be run directly with the manage.py script, provided
that you have checked out the root of the Git repository.

It comes with a prepopulated SQLite database.

# Credits

* Project leader: [Nathan Schneider](http://nathan.cl) (Georgetown)
* Xposition software development: Max Kim, Joseph Ledford (Georgetown)
* Other collaborators/contributors: TODO/see PrepWiki
