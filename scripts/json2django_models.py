import json

file = r'C:\Users\Austin\Desktop\streusle.go.notes.json'

sent_header = ['corpus','sent_id','language','orthography','is_parallel','doc_id','text','word_gloss','sent_gloss','note']

ptoken_header = ['token_start','token_end','adposition','construal','usage','sentence','obj_case','obj_head',
                 'gov_head','gov_obj_syntax','adp_pos','gov_pos','obj_pos','gov_supersense','obj_supersense',
                 'is_gold','note','annotator_group']

# ptoken
token_indices = ''
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
is_gold = 'True'
ptok_note = ''
annotator_cluster = ''


def add_corp_sent(f):
    f.write('\t'.join([corpus,sent_id,language,orthography,is_parallel,doc_id,text,word_gloss,sent_gloss,note])+'\n')


def add_ptoken(f):
    f.write('\t'.join([token_indices,adposition,construal,usage,sentence,obj_case,obj_head,
                 gov_head,gov_obj_syntax,adp_pos,gov_pos,obj_pos,gov_supersense,obj_supersense,
                 is_gold,note,annotator_cluster]) + '\n')


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
                sent_id = sent['sent_id']
                doc_id = ''
                text = sent['text']
                corpus = 'STREUSLE 4.0' # foreign key
                language = 'English'
                orthography = ''
                is_parallel = 'False'
                word_gloss = ''
                sent_gloss = ''
                note = sent['note'] if 'note' in sent else ''
                mwes = sent['mwe']
                add_corp_sent(cs)
                for i in sent['swes']:
                    tok = sent['swes'][i]
                    if tok['lexcat'] in ['P','PRON.POSS','POSS']:
                        if tok['ss']==None or tok['ss2']==None:
                            print(sent_id,tok['lexlemma'])
                            continue
                        # ptoken
                        token_indices = ', '.join([str(x) for x in tok['toknums']])
                        adposition = tok['lexlemma'] # foreign key
                        construal = tok['ss']+'--'+tok['ss2'] # foreign key
                        usage = adposition+':'+construal # foreign key
                        sentence = sent_id # foreign key
                        #print(sentence, adposition)
                        obj_case = 'Genitive' if tok['lexcat']=='PRON.POSS' else 'Accusative'
                        # used to check NoneType
                        govobj = tok['heuristic_relation']
                        hasobj = type(govobj['obj']) is int
                        hasgov = type(govobj['gov']) is int

                        obj_head = govobj['objlemma'] if hasobj else ''
                        gov_head = govobj['govlemma'] if hasgov else ''
                        gov_obj_syntax = govobj['config']
                        adp_pos = sent['toks'][tok['toknums'][0]-1]['upos']
                        gov_pos = sent['toks'][govobj['gov']-1]['upos'] if hasgov else ''
                        obj_pos = sent['toks'][govobj['obj']-1]['upos'] if hasobj else ''
                        gov_supersense = ss(sent, govobj['gov']) if hasgov else ''
                        obj_supersense = ss(sent, govobj['obj']) if hasobj else ''
                        is_gold = 'True'
                        ptok_note = ''
                        annotator_cluster = ''
                        add_ptoken(ptok)

