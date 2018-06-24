import json

file = r'C:\Users\Austin\Desktop\streusle.go.notes.json'

sent_header = ['corpus_name', 'corpus_version', 'sent_id', 'language_name', 'orthography', 'is_parallel', 'doc_id',
               'text', 'tokens', 'word_gloss', 'sent_gloss', 'note', 'mwe_markup']

ptoken_header = ['token_indices', 'adposition_name', 'language_name', 'role_name', 'function_name', 'corpus_name', 'corpus_version', 'sent_id',
                 'obj_case', 'obj_head', 'gov_head', 'gov_obj_syntax', 'adp_pos', 'gov_pos', 'obj_pos', 'gov_supersense',
                 'obj_supersense', 'is_gold', 'annotator_cluster','is_transitive']

default_str = ' '
construal_list = set()
adposition_list = set()
usage_list = set()
supersense_list = set()


# corpus sent
corpus_name = 'streusle'
corpus_version = '4.1'
sent_id = default_str
language_name = 'English'
orthography = default_str
is_parallel = 'False'
doc_id = default_str
text = default_str
tokens = default_str
word_gloss = default_str
sent_gloss = default_str
note = default_str
mwe_markup = default_str


# ptoken
token_indices = default_str
adposition_name = default_str
role_name = default_str
function_name = default_str
corpus_name = 'streusle'
corpus_version = '4.1'
sent_id = default_str
obj_case = default_str
obj_head = default_str
gov_head = default_str
gov_obj_syntax = default_str
adp_pos = default_str
gov_pos = default_str
obj_pos = default_str
gov_supersense = default_str
obj_supersense = default_str
is_gold = 'True'
annotator_cluster = default_str
is_transitive = 'True'



def add_corp_sent(f):
    f.write('\t'.join([corpus_name, corpus_version, sent_id, language_name, orthography, is_parallel, doc_id,
               text, tokens, word_gloss, sent_gloss, note, mwe_markup])+'\n')


def add_ptoken(f):
    f.write('\t'.join([token_indices, adposition_name, language_name, role_name, function_name, corpus_name, corpus_version, sent_id,
                 obj_case, obj_head, gov_head, gov_obj_syntax, adp_pos, gov_pos, obj_pos, gov_supersense,
                 obj_supersense, is_gold, annotator_cluster, is_transitive]) + '\n')


def ss(sent, n):
    supersense = default_str
    for ws in [sent['swes'],sent['smwes']]:
        for tok in ws:
            if n in ws[tok]['toknums']:
                supersense = ws[tok]['ss']
    if supersense==None:
        supersense=default_str
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
                text = sent['text'].replace('"',r'\"')
                tokens = ', '.join(["'"+x['word'].replace("'",r"\'").replace('"',r'\"')+"'" for x in sent['toks']])
                note = sent['note'] if 'note' in sent else default_str
                mwe_markup = sent['mwe']

                add_corp_sent(cs)
                for words in [sent['swes'],sent['smwes'],sent['wmwes']]:
                    for i in words:
                        tok = words[i]
                        if tok['lexcat'] in ['P','PRON.POSS','POSS']:
                            # used to check NoneType
                            govobj = tok['heuristic_relation']
                            hasobj = type(govobj['obj']) is int
                            hasgov = type(govobj['gov']) is int

                            # assign fields
                            token_indices = ', '.join([str(x) for x in tok['toknums']])
                            adposition_name = tok['lexlemma']
                            role_name = tok['ss'].replace('p.','')
                            function_name = '??' if tok['ss'] == '??' else tok['ss2'].replace('p.', '')
                            obj_case = 'ACCUSATIVE' if not tok['lexcat']=='PRON.POSS' else 'GENITIVE'
                            obj_head = govobj['objlemma'] if hasobj else default_str
                            gov_head = govobj['govlemma'] if hasgov else default_str
                            gov_obj_syntax = govobj['config']
                            adp_pos = sent['toks'][tok['toknums'][0] - 1]['upos']
                            gov_pos = sent['toks'][govobj['gov'] - 1]['upos'] if hasgov else default_str
                            obj_pos = sent['toks'][govobj['obj'] - 1]['upos'] if hasobj else default_str
                            gov_supersense = ss(sent, govobj['gov']) if hasgov else default_str
                            obj_supersense = ss(sent, govobj['obj']) if hasobj else default_str
                            annotator_cluster = tok['annotator_cluster'] if 'annotator_cluster' in tok else default_str
                            is_transitive = str(hasobj)
                            add_ptoken(ptok)

                            morphtype = 'standalone_preposition' if not tok['lexlemma']=="'s" else 'suffix'

                            adposition_list.add((adposition_name,language_name,morphtype,is_transitive,obj_case,'0'))
                            construal_list.add(role_name+'--'+function_name)
                            usage_list.add((adposition_name,role_name,function_name,obj_case,'0'))
                            supersense_list.add(role_name)
                            supersense_list.add(function_name)

with open('adpositions.tsv', 'w') as f:
    f.write('name\tlanguage_name\tmorphtype\ttransitivity\tobj_case\trevision_number' + '\n')
    for a in adposition_list:
        f.write('\t'.join(a)+'\n')
with open('construals.tsv', 'w') as f:
    f.write('role\tfunction' + '\n')
    for c in construal_list:
        f.write(c.replace('--','\t') + '\n')
with open('usages.tsv', 'w') as f:
    f.write('adposition_name\trole_name\tfunction_name\tobj_case\trevision_number' + '\n')
    for u in usage_list:
        f.write('\t'.join(u)+'\n')
with open('supersenses.tsv', 'w') as f:
    f.write('name\tdescription\tslug\trevision_number' + '\n')
    for s in supersense_list:
        f.write(s+'\t'+' '+'\t'+s+'0\n')


