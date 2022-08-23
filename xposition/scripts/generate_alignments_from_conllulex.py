"""
This script will update the Alignment Models (ParallelSentenceAlignment and ParallelPTokenAlignment) directly in the database.
Input: the conllulex file containing the alignments to English, and the language 1 and language 2 pairs.
NOTE: Alignments are read only off the other language's (i.e non-English) conllulex file, which is assumed to have all the sentence / token alignment info
TODO: Language pairs where English is not one of the pair.
"""
import os, sys
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "xp.settings")

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

import argparse
import conllu
import warnings

from wiki.plugins.metadata.models import CorpusSentence,ParallelSentenceAlignment,PTokenAnnotation,ParallelPTokenAlignment

def generate_alignments(conllulexfile,language1,language2):

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

    for sent in data:
        en_sent_id = sent.metadata['en_sent_id'].strip()
        sent_id = sent.metadata['sent_id'].strip()

        try:
            # Get the sentence objects first..
            engsentobj = CorpusSentence.objects.get(sent_id=en_sent_id)
            sentobj = CorpusSentence.objects.get(sent_id=sent_id)

            for token in sent:
                if token['misc'] != '_':
                    if token['misc'] is not None and 'AlignedAdposition' in token['misc'].keys() and token['misc']['AlignedAdposition'] != 'None':

                        alignedadposition = token['misc']['AlignedAdposition']
                        alignedadposition = alignedadposition.replace('_',' ').strip()
                        alignedtokid = token['misc']['AlignedTokId']
                        alignedtokid = alignedtokid.replace(',',' ').strip()

                        adposition = token['form'].strip()
                        tokid = str(token['id'])

                        # Get the token objects
                        engtokenobj = PTokenAnnotation.objects.get(sentence=engsentobj,main_subtoken_string=alignedadposition,main_subtoken_indices=alignedtokid)
                        tokenobj = PTokenAnnotation.objects.get(sentence=sentobj,main_subtoken_string=adposition,main_subtoken_indices=tokid)

                        # remove the token alignments first - these are two way
                        objs = ParallelPTokenAlignment.objects.filter(source_example=engtokenobj)

                        # delete only those objects in the language pair
                        for obj in objs:
                            if obj.target_example.sentence.language.slug in (language1,language2):
                                obj.delete()

                        objs = ParallelPTokenAlignment.objects.filter(source_example=tokenobj)
                        for obj in objs:
                            if obj.target_example.sentence.language.slug in (language1,language2):
                                obj.delete()

                        # then create the new ones - two way
                        ParallelPTokenAlignment.objects.create(source_example=engtokenobj,target_example=tokenobj)
                        ParallelPTokenAlignment.objects.create(source_example=tokenobj, target_example=engtokenobj)

            # first delete existing alignments, if any
            objs = ParallelSentenceAlignment.objects.filter(source_sentence=sentobj)
            for obj in objs:
                if obj.target_sentence.language.slug in (language1,language2):
                    obj.delete()
            objs = ParallelSentenceAlignment.objects.filter(source_sentence=engsentobj) # two way alignments
            for obj in objs:
                if obj.target_sentence.language.slug in (language1,language2):
                    obj.delete()


            # then add the alignment
            ParallelSentenceAlignment.objects.create(source_sentence=engsentobj,target_sentence=sentobj)
            ParallelSentenceAlignment.objects.create(source_sentence=sentobj, target_sentence=engsentobj)

        except Exception as e:
            if 'matching query does not exist' in str(e):
                warnings.warn('Warning: No CorpusSentence or Adposition Token for sentence pairs %s \t %s ' % (sent_id,en_sent_id))
                continue
            else:
                print ('Error with sentence pairs %s \t %s \n Error is: %s' % (sent_id,en_sent_id,str(e)),file=sys.stderr)
                raise


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('conllulexfile', type=str, help='location of conllulex file with alignments')
    parser.add_argument('language1', type=str, help='first language in the pair')
    parser.add_argument('language2', type=str, help='second language in the pair')

    args = parser.parse_args()

    if args.language1.strip().lower() not in ('zh', 'en', 'hi', 'de', 'ko','he'):
        print('Language 1 must be one of zh,en,hi,de,ko,he', file=sys.stderr)
        return

    if args.language1.strip().lower() not in ('zh', 'en', 'hi', 'de', 'ko','he'):
        print('Language 2 must be one of zh,en,hi,de,ko,he', file=sys.stderr)
        return

    generate_alignments(args.conllulexfile,args.language1,args.language2)


if __name__ == "__main__":
    main()
