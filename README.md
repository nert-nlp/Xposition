Installation
============

Requires Python 3.6+

Once you've cloned the git repository, you'll need to install the __django-wiki__ and __django-categories__ libraries (and their dependencies):

    pip install wiki
    pip install django-categories
    pip install django-bitfield
    pip install django-import-export

Testing
===========

This project can be run directly with the manage.py script, provided
that you have checked out the root of the Git repository.

It comes with a prepopulated SQLite database.

Running
-------

There is a settings file called `unversioned.py` with secret information that is therefore not included in this repository. 
It should go in `testproject/testproject/settings/` and set the variable `SECRET_KEY`.

Then you should be able to run the server like this:

    python manage.py runserver

If you are running on Windows, this may give an error about `wiki.plugins.categories`. This is because a Unix symlink is not interpreted propertly by Windows. In the `testproject` directory, remove `wiki` and replace it with a Windows symlink: `mklink /D wiki ..\wiki`

When the server first starts, it should print a warning about outstanding migrations. Exit the server, then run

    python manage.py migrate
    
to update the database to reflect the current schema required by the app.

Configuring for development
---------------------------

Edit `testproject/testproject/settings/local.py` by commenting out the last line and uncommenting the line with

```py
from .dev import *
```

Login
-----

Django admin:

  * Username: `admin`
  * Password: `admin`

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

## Credits

* Project leader: [Nathan Schneider](http://nathan.cl) (Georgetown)
* Xposition software development: Max Kim, Joseph Ledford (Georgetown)
* Other collaborators/contributors: TODO/see PrepWiki
>>>>>>> 91ff73518db584d3382b199f62976f2bd988500f
