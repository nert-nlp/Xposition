import argparse
import sqlite3
import datetime
import os
import subprocess
from shutil import copyfile
import re


def apply_markup_replacements(text):
    r"""Performs the following substring replacements within macros:

        \\_ -> \_
        \"  -> "

    """
    new_text = []
    macro_status = []
    quote_status = False
    for i, c in enumerate(text):
        if c == "[" and re.match(r"^(ss|p|pspecial|ex|gex|exref)", text[i+1:]):
            macro_status.append("macro")
        elif c == "[":
            macro_status.append("nonmacro")
        elif c == "]":
            macro_status.pop()
        elif c == '"' and macro_status and macro_status[-1] == "macro":
            quote_status = not quote_status
        elif c == '\\' and quote_status:
            continue
        elif macro_status and macro_status[-1] == "macro" and c == '\\' and text[i+1:i+3] == '\\_':
            continue
        elif macro_status and macro_status[-1] == "macro" and c == '\\' and text[i+1:i+2] == '"':
            continue
        new_text.append(c)
    return "".join(new_text)


def remove_backslashes_in_macros_inplace(args):
    """Ideally we would have created a new article revision, but this is complicated, so we just update the content
    of the latest revision and leave a message."""
    conn = sqlite3.connect(args.db_name)
    cursor = conn.cursor()
    # get just the latest revision for each article
    latest_revision_query = '''
SELECT *
FROM wiki_articlerevision T1
WHERE revision_number = (
   SELECT max(revision_number)
   FROM wiki_articlerevision T2
   WHERE T1.article_id=T2.article_id
)
'''
    rows = list(cursor.execute(latest_revision_query))
    for row in rows:
        new_text = apply_markup_replacements(row[8])

        if len(new_text) != len(row[8]):

            # update the revision
            cursor.execute('''UPDATE wiki_articlerevision SET content=?, user_message=? WHERE id=?''',
                           (new_text, "((This revision was updated by 2019_upgrade_fixes.py)) " + row[6], row[-1]))

            print("Updated markup for {} [{}]".format(row[4], row[9]))
            if args.diff_file_dir:
                old_filepath = args.diff_file_dir + os.sep + row[4] + '.old'
                new_filepath = args.diff_file_dir + os.sep + row[4] + '.new'
                with open(old_filepath, 'w') as f:
                    f.write(row[8])
                with open(new_filepath, 'w') as f:
                    f.write(new_text)
                try:
                    print("\tDiff:")
                    subprocess.call(["diff", old_filepath, new_filepath])
                except:
                    pass
                print("\tSee new and old files at '{}'".format(args.diff_file_dir + os.sep + row[4] + "{.old, .new}"))

    conn.commit()
    conn.close()


def remove_backslashes_in_macros(args):
    conn = sqlite3.connect(args.db_name)
    cursor = conn.cursor()
    # get just the latest revision for each article
    latest_revision_query = '''
SELECT *
FROM wiki_articlerevision T1
WHERE revision_number = (
   SELECT max(revision_number)
   FROM wiki_articlerevision T2
   WHERE T1.article_id=T2.article_id
)
'''
    raise NotImplemented("This method isn't implemented properly. Use `remove_backslashes_in_macros_inplace`")
    rows = list(cursor.execute(latest_revision_query))
    for row in rows:
        new_text = apply_markup_replacements(row[8])

        if len(new_text) != len(row[8]):
            now = datetime.datetime.now()
            print("Detected difference for {} [{}]".format(row[4], row[9]))

            # create a new revision
            cursor.execute('''INSERT INTO wiki_articlerevision
            (previous_revision_id, locked, created, deleted, title, 
            automatic_log, user_message, modified, content, article_id, 
            revision_number, user_id, ip_address)
            VALUES (?,?,?,?,?, ?,?,?,?,?, ?,?,?)''',
                           (row[-1], 0, now, row[3], row[4],
                            '', 'Backslashes removed by 2019_upgrade_fixes.py', now, new_text, row[9],
                            row[10] + 1, None, None))

            # save the new revision's id
            new_article_revision_id = cursor.lastrowid

            # set the article's current revision to the new revision
            cursor.execute('''UPDATE wiki_article SET current_revision_id=? WHERE id=?''',
                           (new_article_revision_id, row[9]))

            # make sure any associated metadata is also associated with the new revision
            # (cf. Metadata.link_current_to_article_revision)
            prev_metas = cursor.execute('''SELECT template, name, description 
            FROM metadata_metadatarevision 
            WHERE article_revision_id=?''', (row[-1],))
            for prev_meta in list(prev_metas):
                cursor.execute('''INSERT INTO metadata_metadatarevision 
                (template, name, article_revision_id, description)
                VALUES (?,?,?,?)''', (prev_meta[0], prev_meta[1], new_article_revision_id, prev_meta[2]))
                print(prev_meta, cursor.lastrowid)

            print("Wrote changes to {} [{}]".format(row[4], row[9]))
            if args.diff_file_dir:
                with open(args.diff_file_dir + os.sep + row[4] + '.old', 'w') as f:
                    f.write(row[8])
                with open(args.diff_file_dir + os.sep + row[4] + '.new', 'w') as f:
                    f.write(new_text)

    conn.commit()
    conn.close()

def backup_database(args):
    print("Backing up database to " + args.db_name + ".backup")
    copyfile(args.db_name, args.db_name + ".backup")

def main(args):
    backup_database(args)
    remove_backslashes_in_macros_inplace(args)

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("db_name")
    p.add_argument("--diff-file-dir", default=None,
                   help="If supplied, produces .old and .new versions of the contents of each article that was affected")
    args = p.parse_args()
    args.diff_file_dir = (args.diff_file_dir[:-1]
                          if args.diff_file_dir and args.diff_file_dir[-1] == os.sep
                          else args.diff_file_dir)

    main(args)
