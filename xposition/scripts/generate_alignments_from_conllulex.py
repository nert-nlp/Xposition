"""
This script will update the Alignment Models (ParallelSentenceAlignment and ParallelPTokenAlignment) directly in the database.
Input: the conllulex file containing the alignments to English, and the language 1 and language 2 pair slug values.
NOTE: Alignments are read only off the other language's (i.e non-English) conllulex file, which is assumed to have all the sentence / token alignment info
IMPORTANT: Make sure the conllulex file contains all the alignments for the language pair. Piece-wise loading of alignments via conllulex is not supported (too many tricky use cases).
           The loading operation will truncate and load all alignments for the language pair, everytime.

TODO: Language pairs where English is not one of the pair.
"""
import os, sys
sys.path.insert(0,'../xposition')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "xp.settings")

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

import argparse
import conllu
import warnings

from wiki.plugins.metadata.models import CorpusSentence,ParallelSentenceAlignment,PTokenAnnotation,ParallelPTokenAlignment

def generate_alignments(conllulexfile,language1,language2,truncate=True):

    def read_conllulex(conllulexfile):
        fields = tuple(
            list(conllu.parser.DEFAULT_FIELDS)
            + [
                "smwe",  # 10
                "lexcat",  # 11
                "lexlemma",  # 12
                "ss",  # 13
                "ss2",  # 14
                "wmwe",  # 15
                "wcat",  # 16
                "wlemma",  # 17
                "lextag",  # 18
            ]
        )

        with open(conllulexfile, "r", encoding="utf-8") as f:
            return conllu.parse(f.read(), fields=fields)

    data = read_conllulex(conllulexfile)


    if truncate == True:
        ParallelSentenceAlignment.objects.filter(target_sentence__language__slug=language2).delete()
        ParallelSentenceAlignment.objects.filter(target_sentence__language__slug=language1).delete()
        ParallelPTokenAlignment.objects.filter(target_example__sentence__language__slug=language1).delete()
        ParallelPTokenAlignment.objects.filter(target_example__sentence__language__slug=language2).delete()

    for sent in data:
        en_sent_id = sent.metadata['en_sent_id'].strip()
        sent_id = sent.metadata['sent_id'].strip()

        try:
            # Get the sentence objects first..
            engsentobj = CorpusSentence.objects.get(sent_id=en_sent_id)
            sentobj = CorpusSentence.objects.get(sent_id=sent_id)
        except Exception as e:
            if 'matching query does not exist' in str(e):
                warnings.warn('Warning: No CorpusSentence object for sentence pairs %s \t %s ' % (sent_id,en_sent_id))
                continue
            else:
                print ('Error with sentence pairs %s \t %s \n Error is: %s' % (sent_id,en_sent_id,str(e)),file=sys.stderr)
                raise


        for token in sent:
            if token['misc'] != '_':
                if token['misc'] is not None and 'AlignedAdposition' in token['misc'].keys() and token['misc']['AlignedAdposition'] != 'None':

                    alignedtokid = token['misc']['AlignedTokId']
                    alignedtokid = alignedtokid.replace(',',' ').strip()

                    tokid = str(token['id'])

                    # Get the token objects
                    try:
                        engtokenobj = PTokenAnnotation.objects.get(sentence=engsentobj,main_subtoken_indices=alignedtokid)
                        tokenobj = PTokenAnnotation.objects.get(sentence=sentobj,main_subtoken_indices=tokid)
                    except Exception as e:
                        if 'matching query does not exist' in str(e):
                            warnings.warn('Warning: No Token object ID: %s \t %s for sentence pairs %s \t %s ' % (tokid,alignedtokid,sent_id, en_sent_id))
                            continue
                        else:
                            print('Error with sentence pairs %s \t %s \n Error is: %s' % (sent_id, en_sent_id, str(e)), file=sys.stderr)
                            raise

                    # then create the new ones - two way
                    ParallelPTokenAlignment.objects.create(source_example=engtokenobj,target_example=tokenobj)
                    ParallelPTokenAlignment.objects.create(source_example=tokenobj, target_example=engtokenobj)

        # then add the alignment
        ParallelSentenceAlignment.objects.create(source_sentence=engsentobj,target_sentence=sentobj)
        ParallelSentenceAlignment.objects.create(source_sentence=sentobj, target_sentence=engsentobj)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('conllulexfile', type=str, help='location of conllulex file with alignments')
    parser.add_argument('language1', type=str, help='first language in the pair')
    parser.add_argument('language2', type=str, help='second language in the pair')

    args = parser.parse_args()

    if '.conllulex' not in args.conllulexfile:
        print ('File must be conllulex format',file=sys.stderr)
        return

    if args.language1.strip().lower() not in ('zh', 'en', 'hi', 'de', 'ko','he'):
        print('Language 1 must be one of zh,en,hi,de,ko,he', file=sys.stderr)
        return

    if args.language1.strip().lower() not in ('zh', 'en', 'hi', 'de', 'ko','he'):
        print('Language 2 must be one of zh,en,hi,de,ko,he', file=sys.stderr)
        return

    generate_alignments(args.conllulexfile,args.language1,args.language2)


if __name__ == "__main__":
    main()
