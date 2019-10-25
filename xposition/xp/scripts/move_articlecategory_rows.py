import os
import argparse
from shutil import copyfile
from django.db import connection
import django

def copy_rows():
    # just need any model so we can execute raw sql
    cursor = connection.cursor()
    cursor.execute('INSERT INTO categories_articlecategory SELECT * FROM wiki_articlecategory;')

def backup_database(args):
    print("Backing up database to " + args.db_name + ".backup")
    copyfile(args.db_name, args.db_name + ".backup")

def main(args):
    backup_database(args)
    copy_rows()
    print(f"Rows moved. Consider deleting {args.db_name}.backup.")

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "xp.settings")
    django.setup()
    p = argparse.ArgumentParser(description=("Moves rows from wiki_articlecategory to category_articlecategory"))
    p.add_argument("db_name")
    args = p.parse_args()
    main(args)
