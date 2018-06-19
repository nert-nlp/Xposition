import json

file = r'C:\Users\Austin\Desktop\streusle.go.notes.json'

sent_header = ['corpus_name', 'corpus_version', 'sent_id', 'language_name', 'orthography', 'is_parallel', 'doc_id',
               'text', 'tokens', 'word_gloss', 'sent_gloss', 'note', 'mwe_markup']

ptoken_header = ['token_indices', 'adposition_name', 'construal_name', 'corpus_name', 'corpus_version', 'sent_id',
                 'obj_case', 'obj_head', 'gov_head', 'gov_obj_syntax', 'adp_pos', 'gov_pos', 'obj_pos', 'gov_supersense',
                 'obj_supersense', 'is_gold', 'annotator_cluster']


# corpus
corpus_name = 'streusle'
corpus_version = '4.1'
sent_id = ''
language_name = 'English'
orthography = ''
is_parallel = 'False'
doc_id = ''
text = ''
tokens = ''
word_gloss = ''
sent_gloss = ''
note = ''
mwe_markup = ''


# ptoken
token_indices = ''
adposition_name = ''
construal_name = ''
corpus_name = 'streusle'
corpus_version = '4.1'
sent_id = ''
obj_case = ''
obj_head = ''
gov_head = ''
gov_obj_syntax = ''
adp_pos = ''
gov_pos = ''
obj_pos = ''
gov_supersense = ''
obj_supersense = ''
is_gold = 'True'
annotator_cluster = ''



def add_corp_sent(f):
    f.write('\t'.join([corpus_name, corpus_version, sent_id, language_name, orthography, is_parallel, doc_id,
               text, tokens, word_gloss, sent_gloss, note, mwe_markup])+'\n')


def add_ptoken(f):
    f.write('\t'.join([token_indices, adposition_name, construal_name, corpus_name, corpus_version, sent_id,
                 obj_case, obj_head, gov_head, gov_obj_syntax, adp_pos, gov_pos, obj_pos, gov_supersense,
                 obj_supersense, is_gold, annotator_cluster]) + '\n')


def ss(sent, n):
    supersense = ''
    for ws in [sent['swes'],sent['smwes']]:
        for tok in ws:
            if n in ws[tok]['toknums']:
                supersense = ws[tok]['ss']
    if supersense==None:
        supersense=''
    return supersense

with open(file, encoding='utf8') as f:
    with open('corpus_sents.tsv', 'w', encoding='utf8') as cs:
        with open('ptokens.tsv', 'w', encoding='utf8') as ptok:
            cs.write('\t'.join(sent_header) + '\n')
            ptok.write('\t'.join(ptoken_header) + '\n')
            data = json.load(f)
            for sent in data:
                # assign fields
                sent_id = sent['sent_id']
                doc_id = sent['sent_id'].split('-')[0]+'-'+sent['sent_id'].split('-')[1]
                text = sent['text']
                tokens = ', '.join(["'"+x['word'].replace("'",r"\'")+"'" for x in sent['toks']])
                note = sent['note'] if 'note' in sent else ''
                mwe_markup = sent['mwe']

                add_corp_sent(cs)

                for i in sent['swes']:
                    tok = sent['swes'][i]
                    if tok['lexcat'] in ['P','PRON.POSS','POSS']:
                        # used to check NoneType
                        govobj = tok['heuristic_relation']
                        hasobj = type(govobj['obj']) is int
                        hasgov = type(govobj['gov']) is int

                        # assign fields
                        token_indices = ', '.join([str(x) for x in tok['toknums']])
                        adposition_name = tok['lexlemma']
                        construal_name = '??' if tok['ss'] == '??' else tok['ss']+'--'+tok['ss2']
                        obj_case = 'Accusative' if not tok['lexcat']=='PRON.POSS' else 'Genitive'
                        obj_head = govobj['objlemma'] if hasobj else ''
                        gov_head = govobj['govlemma'] if hasgov else ''
                        gov_obj_syntax = govobj['config']
                        adp_pos = sent['toks'][tok['toknums'][0] - 1]['upos']
                        gov_pos = sent['toks'][govobj['gov'] - 1]['upos'] if hasgov else ''
                        obj_pos = sent['toks'][govobj['obj'] - 1]['upos'] if hasobj else ''
                        gov_supersense = ss(sent, govobj['gov']) if hasgov else ''
                        obj_supersense = ss(sent, govobj['obj']) if hasobj else ''
                        annotator_cluster = tok['annotator_cluster'] if 'annotator_cluster' in tok else ''
                        add_ptoken(ptok)

