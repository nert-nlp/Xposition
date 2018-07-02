import os, django
os.chdir('..\scripts')
# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "testproject.testproject.settings")
# django.setup()

from wiki.plugins.metadata import models as ms

file = 'streusle.go.notes.json'

sent_header = ['corpus_name', 'corpus_version', 'sent_id', 'language_name', 'orthography', 'is_parallel', 'doc_id',
               'text', 'tokens', 'word_gloss', 'sent_gloss', 'note', 'mwe_markup']

ptoken_header = ['token_indices', 'adposition_name', 'language_name', 'role_name', 'function_name', 'special', 'corpus_name',
                 'corpus_version', 'sent_id',
                 'obj_case', 'obj_head', 'gov_head', 'gov_obj_syntax', 'gov_head_index', 'obj_head_index', 'is_typo', 'is_abbr', 'adp_pos', 'gov_pos', 'obj_pos',
                 'gov_supersense',
                 'obj_supersense', 'is_gold', 'annotator_cluster', 'is_transitive', 'adposition_id', 'construal_id',
                 'usage_id']

DEFAULT_STR = ' '
construal_list = set()
adposition_list = set()
usage_list = set()
supersense_list = set()
adp_trans = set()
adp_intrans = set()

# corpus sent
corpus_name = 'streusle'
corpus_version = '4.1'
sent_id = DEFAULT_STR
language_name = 'English'
orthography = DEFAULT_STR
is_parallel = '0'
doc_id = DEFAULT_STR
text = DEFAULT_STR
tokens = DEFAULT_STR
word_gloss = DEFAULT_STR
sent_gloss = DEFAULT_STR
note = DEFAULT_STR
mwe_markup = DEFAULT_STR

# ptoken
token_indices = DEFAULT_STR
adposition_name = DEFAULT_STR
role_name = DEFAULT_STR
function_name = DEFAULT_STR
special = DEFAULT_STR
corpus_name = 'streusle'
corpus_version = '4.1'
sent_id = DEFAULT_STR
obj_case = DEFAULT_STR
obj_head = DEFAULT_STR
gov_head = DEFAULT_STR
gov_obj_syntax = DEFAULT_STR
adp_pos = DEFAULT_STR
gov_pos = DEFAULT_STR
obj_pos = DEFAULT_STR
gov_supersense = DEFAULT_STR
obj_supersense = DEFAULT_STR
is_gold = '1'
annotator_cluster = DEFAULT_STR
is_transitive = '1'
adposition_id = DEFAULT_STR
construal_id = DEFAULT_STR
usage_id = DEFAULT_STR
gov_head_index = DEFAULT_STR
obj_head_index = DEFAULT_STR
is_typo = '0'
is_abbr = '0'

adp_memo = {}
for adp in ms.Adposition.objects.all():
    adp_memo[(adp.current_revision.metadatarevision.adpositionrevision.name,
              adp.current_revision.metadatarevision.adpositionrevision.lang.name)] = str(adp.pk)
    # print(adp.current_revision.metadatarevision.adpositionrevision.name)
ss_memo = {}
for ss in ms.Supersense.objects.all():
    x = ss.current_revision.metadatarevision.supersenserevision.name
    ss_memo[x] = str(ss.pk)
con_memo = {}
for c in ms.Construal.objects.all():
    con_memo[(c.role.current_revision.metadatarevision.supersenserevision.name if c.role else DEFAULT_STR,
              c.function.current_revision.metadatarevision.supersenserevision.name if c.function else DEFAULT_STR,
              c.special if c.special else DEFAULT_STR)] = str(c.pk)
us_memo = {}
for u in ms.Usage.objects.all():
    us_memo[(u.current_revision.metadatarevision.usagerevision.adposition.current_revision.metadatarevision.adpositionrevision.name,
             u.current_revision.metadatarevision.usagerevision.construal.pk)] \
        = str(u.pk)

def clean_adp(language_name, adposition_name):
    if (adposition_name,language_name) in adp_memo:
        return adp_memo[(adposition_name,language_name)]
    else:
        return DEFAULT_STR

def clean_con(role_name, function_name, special):
    if (role_name, function_name, special) in con_memo:
        return con_memo[(role_name, function_name, special)]
    else:
        return DEFAULT_STR

def clean_us(adposition_name, construal_id):
    if (adposition_name, construal_id) in us_memo:
        return us_memo[(adposition_name, construal_id)]
    else:
        return DEFAULT_STR

def clean_ss(name):
    if name in ss_memo:
        return ss_memo[name]
    else:
        return DEFAULT_STR

def add_corp_sent(f):
    f.write('\t'.join([globals()[s] for s in sent_header]) + '\n')


def add_ptoken(f):
    f.write('\t'.join([globals()[s] for s in ptoken_header]) + '\n')


def get_ss(sent, n):
    supersense = DEFAULT_STR
    for ws in [sent['swes'], sent['smwes']]:
        for tok in ws:
            if n in ws[tok]['toknums']:
                supersense = ws[tok]['ss']
    if supersense == None:
        supersense = DEFAULT_STR
    return supersense

num_lines = len([line for line in open(file, encoding='utf8') if '"sent_id"' in line])

with open(file, encoding='utf8') as f:
    with open('corpus_sents.tsv', 'w', encoding='utf8') as cs:
        with open('ptokens.tsv', 'w', encoding='utf8') as ptok:
            cs.write('\t'.join(sent_header) + '\n')
            ptok.write('\t'.join(ptoken_header) + '\n')
            data = json.load(f)
            for i,sent in enumerate(data):
                #if i%(num_lines/100) == 0:
                # print(str(i),'/',str(num_lines),' '+str(100*i/num_lines)+'%')
                # assign fields
                sent_id = sent['sent_id']
                doc_id = sent['sent_id'].split('-')[0] + '-' + sent['sent_id'].split('-')[1]
                text = sent['text'].replace('"', r'\"')
                tokens = ' '.join([x['word'].replace("'", r"\'").replace('"', r'\"') for x in sent['toks']])
                note = sent['note'] if 'note' in sent else DEFAULT_STR
                mwe_markup = sent['mwe']

                add_corp_sent(cs)

                for words in [sent['swes'], sent['smwes'], sent['wmwes']]:
                    for i in words:
                        if words[i]['lexcat'] in ['P', 'PRON.POSS', 'POSS']:
                            tok_sem = words[i]                                   # token semantic features
                            tok_morph = sent['toks'][tok_sem['toknums'][0] - 1]  # token morphological/syntactic features
                            # used to check NoneType
                            govobj = tok_sem['heuristic_relation']
                            hasobj = type(govobj['obj']) is int
                            hasgov = type(govobj['gov']) is int

                            # assign fields
                            token_indices = ' '.join([str(x) for x in tok_sem['toknums']])
                            adposition_name = tok_sem['lexlemma'].replace(' ','_')
                            if '?' in tok_sem['ss'] or '`' in tok_sem['ss']:
                                role_name = DEFAULT_STR
                                function_name = DEFAULT_STR
                                special = tok_sem['ss']
                            else:
                                role_name = tok_sem['ss'].replace('p.', '')
                                function_name = tok_sem['ss2'].replace('p.', '')
                                special = DEFAULT_STR
                            obj_case = 'Accusative' if not tok_sem['lexcat'] in ['PRON.POSS','POSS'] else 'Genitive'
                            obj_head = govobj['objlemma'] if hasobj else DEFAULT_STR
                            gov_head = govobj['govlemma'] if hasgov else DEFAULT_STR
                            gov_obj_syntax = govobj['config']
                            adp_pos = tok_morph['upos']
                            gov_pos = sent['toks'][govobj['gov'] - 1]['upos'] if hasgov else DEFAULT_STR
                            obj_pos = sent['toks'][govobj['obj'] - 1]['upos'] if hasobj else DEFAULT_STR
                            gov_supersense = get_ss(sent, govobj['gov']) if hasgov else DEFAULT_STR
                            obj_supersense = get_ss(sent, govobj['obj']) if hasobj else DEFAULT_STR
                            annotator_cluster = tok_sem['annotator_cluster'] if 'annotator_cluster' in tok_sem else DEFAULT_STR
                            is_transitive = '1' if hasobj else '0'
                            adposition_id = clean_adp(language_name, adposition_name)
                            construal_id = clean_con(role_name, function_name, special)
                            usage_id = clean_us(adposition_name, int(construal_id)) if not construal_id==DEFAULT_STR \
                                else DEFAULT_STR
                            gov_head_index = str(govobj['gov']) if hasgov else DEFAULT_STR
                            obj_head_index = str(govobj['obj']) if hasobj else DEFAULT_STR
                            if 'feats' in tok_morph and tok_morph['feats']:
                                is_typo = '1' if 'Typo=Yes' in tok_morph['feats'] else '0'
                                is_abbr = '1' if 'Abbr=Yes' in tok_morph['feats'] else '0'
                            add_ptoken(ptok)

                            morphtype = 'standalone_preposition' if not tok_sem['lexlemma'] == "'s" else 'suffix'
                            if hasobj:
                                adp_trans.add(adposition_name)
                            else:
                                adp_intrans.add(adposition_name)
                            adposition_list.add((adposition_name, language_name, morphtype, obj_case))
                            construal_list.add((role_name,function_name,special,clean_ss(role_name), clean_ss(function_name)))
                            usage_list.add((adposition_name, role_name, function_name, obj_case, adposition_id, construal_id))
                            if not '?' in role_name and not '`' in role_name and not role_name==' ':
                                supersense_list.add(role_name)
                            if not '?' in function_name and not '`' in function_name and not function_name==' ':
                                supersense_list.add(function_name)
adp_transitivity = {}
for a in adposition_list:
    adp = a[0]
    adp_transitivity[adp] = 'sometimes_transitive' if (adp in adp_trans and adp in adp_intrans) \
                            else 'always_transitive' if adp in adp_trans \
                            else 'always_intransitive'

with open('adposition_revisions.tsv', 'w') as f:
    f.write('adposition_name\tlanguage_name\tmorphtype\tobj_case\ttransitivity' + '\n')
    for a in adposition_list:
        f.write('\t'.join(a) +'\t'+adp_transitivity[a[0]]+'\n')
with open('construals.tsv', 'w') as f:
    f.write('role_name\tfunction_name\tspecial\trole_id\tfunction_id' + '\n')
    for c in construal_list:
        f.write('\t'.join(c) + '\n')
with open('usage_revisions.tsv', 'w') as f:
    f.write('adposition_name\trole_name\tfunction_name\tobj_case\tadposition_id\tconstrual_id' + '\n')
    for u in usage_list:
        f.write('\t'.join(u) + '\n')
with open('supersense_revisions.tsv', 'w') as f:
    f.write('supersense_name' + '\n')
    for s in supersense_list:
        f.write(s  + '\n')
