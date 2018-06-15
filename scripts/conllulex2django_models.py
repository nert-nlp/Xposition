

file = r'C:\Users\Austin\Desktop\streusle.conllulex'

sent_header = ['corpus','sent_id','language','orthography','is_parallel','doc_id','text','word_gloss','sent_gloss','note']

ptoken_header = ['token_start','token_end','adposition','construal','usage','sentence','obj_case','obj_head',
                 'gov_head','gov_obj_syntax','adp_pos','gov_pos','obj_pos','gov_supersense','obj_supersense',
                 'is_gold','note','annotator_group']

sents = []
ptokens = []


# corpus sent
sent_id = ''
doc_id = ''
text = ''
corpus = 'STREUSLE'
language ='English'
orthography = ''
is_parallel = False
word_gloss = ''
sent_gloss = ''
note = ''


# ptoken
token_start = -1
token_end = -1
adposition = ''
construal = ''
usage = ''
sentence = ''
obj_case = ''
obj_head = ''
gov_head = ''
gov_obj_syntax = ''
adp_pos = ''
gov_pos = ''
obj_pos = ''
gov_supersense = ''
obj_supersense = ''
is_gold = ''
ptok_note = ''
annotator_group = ''


def add_corp_sent(f):
    f.write('\t'.join([corpus,sent_id,language,orthography,is_parallel,doc_id,text,word_gloss,sent_gloss,note])+'\n')


def add_ptoken(f):
    f.write('\t'.join([token_start,token_end,adposition,construal,usage,sentence,obj_case,obj_head,
                 gov_head,gov_obj_syntax,adp_pos,gov_pos,obj_pos,gov_supersense,obj_supersense,
                 is_gold,note,annotator_group]) + '\n')


with open(file) as f:
    with open('corpus_sents.tsv', 'w') as cs:
        with open('ptokens.tsv', 'w') as ptok:
            for line in f:
                if line.startswith('# newdoc id = '):
                    doc_id = line.replace('# newdoc id = ','').strip()
                elif line.startswith('# sent_id = '):
                    #sent_id = line.replace('# sent_id = ','').strip()
                    continue
                elif line.startswith('# text = '):
                    text = line.replace('# text = ','').strip()
                elif line.startswith('# streusle_sent_id = '):
                    sent_id = line.replace('# streusle_sent_id = ','').strip()
                elif line.startswith('# mwe = '):
                    mwes = line.replace('# mwe = ','').strip()
                elif line.strip() == '':
                    continue
                else:
                    for val in line.split('\t'):
                        ...
