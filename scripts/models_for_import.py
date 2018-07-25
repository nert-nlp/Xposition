import os, json
os.chdir('../scripts')

from wiki.plugins.metadata import models as ms

dir = 'json'

file = 'streusle.go.notes.json'

corpus_sentences = []
ptoken_annotations = []

corpus_sentences_header = ['corpus_name', 'corpus_version', 'sent_id', 'language_name', 'orthography', 'is_parallel', 'doc_id',
               'text', 'tokens', 'word_gloss', 'sent_gloss', 'note', 'mwe_markup']

ptoken_header = ['token_indices', 'adposition_name', 'language_name', 'role_name', 'function_name', 'special', 'corpus_name',
                 'corpus_version', 'sent_id',
                 'obj_case', 'obj_head', 'gov_head', 'gov_obj_syntax', 'gov_head_index', 'obj_head_index', 'is_typo', 'is_abbr', 'adp_pos', 'gov_pos', 'obj_pos',
                 'gov_supersense',
                 'obj_supersense', 'is_gold', 'annotator_cluster', 'is_transitive', 'adposition_id', 'construal_id',
                 'usage_id', 'mwe_subtokens', 'main_subtoken_indices', 'main_subtoken_string']

DEFAULT_STR = ' '
construal_set = set()
adposition_set = set()
usage_set = set()
supersense_set = set()
adp_trans = set()
adp_intrans = set()
construal_json = []
adposition_json = []
usage_json = []
supersense_json = [
    {'supersense_name':'Temporal'}, {'supersense_name':'Configuration'}, {'supersense_name':'Participant'}
]

# corpus sent
corpus_name = 'STREUSLE'
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
corpus_name = 'STREUSLE'
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
mwe_subtokens = DEFAULT_STR
main_subtoken_indices = DEFAULT_STR
main_subtoken_string = DEFAULT_STR


class GetIDs:
    adp_memo = {}
    ss_memo = {}
    con_memo = {}
    us_memo = {}

    def __init__(self):
        for adp in ms.Adposition.objects.all():
            self.adp_memo[(adp.current_revision.metadatarevision.adpositionrevision.name,
                      adp.current_revision.metadatarevision.adpositionrevision.lang.name)] = str(adp.pk)
            # print(adp.current_revision.metadatarevision.adpositionrevision.name)

        for ss in ms.Supersense.objects.all():
            x = ss.current_revision.metadatarevision.supersenserevision.name
            self.ss_memo[x] = str(ss.pk)

        for c in ms.Construal.objects.all():
            self.con_memo[(c.role.current_revision.metadatarevision.supersenserevision.name if c.role else DEFAULT_STR,
                      c.function.current_revision.metadatarevision.supersenserevision.name if c.function else DEFAULT_STR,
                      c.special if c.special else DEFAULT_STR)] = str(c.pk)

        for u in ms.Usage.objects.all():
            self.us_memo[(u.current_revision.metadatarevision.usagerevision.adposition.current_revision.metadatarevision.adpositionrevision.name,
                     u.current_revision.metadatarevision.usagerevision.construal.pk)] \
                = str(u.pk)

    def clean_adp(self, language_name, adposition_name):
        if (adposition_name,language_name) in self.adp_memo:
            return self.adp_memo[(adposition_name,language_name)]
        else:
            return '0'

    def clean_con(self, role_name, function_name, special):
        if (role_name, function_name, special) in self.con_memo:
            return self.con_memo[(role_name, function_name, special)]
        else:
            return '0'

    def clean_us(self, adposition_name, construal_id):
        if (adposition_name, construal_id) in self.us_memo:
            return self.us_memo[(adposition_name, construal_id)]
        else:
            return '0'

    def clean_ss(self, name):
        if name in self.ss_memo:
            return self.ss_memo[name]
        else:
            return '0'

def add_corp_sent():
    x = {}
    for s in corpus_sentences_header:
        x[s] = globals()[s]
    corpus_sentences.append(x)


def add_ptoken():
    x = {}
    for s in ptoken_header:
        x[s] = globals()[s]
    ptoken_annotations.append(x)


def get_ss(sent, n):
    supersense = DEFAULT_STR
    for ws in [sent['swes'], sent['smwes']]:
        for tok in ws:
            if n in ws[tok]['toknums']:
                supersense = ws[tok]['ss']
    if supersense == None:
        supersense = DEFAULT_STR
    return supersense

def get_adp(s, lang):
    adp = ms.Adposition.normalize_adp(cls=ms.Adposition,
                                adp=s,
                                language_name=lang)
    adp = adp or s
    adp = adp.replace(' ', '_')
    if adp in ['he', 'it', "it's", 'she', 'there', 'they', 'thier', 'ur', 'we', 'you']:
        adp = "'s"
    return adp


def main_indices(token_indices=''):
    x = []
    for i in token_indices.split():
        # only add direct successor
        if not x or int(i) == int(x[-1]) + 1:
            x.append(i)
        else:
            break
    return ' '.join(x)

def main_string(mwe_subtokens='', token_indices=''):
    x = main_indices(token_indices).split()
    return ' '.join(mwe_subtokens.split()[:len(x)])

ids = GetIDs()

with open(file, encoding='utf8') as f:
    data = json.load(f)
    for i, sent in enumerate(data):
        if i%500==0:
            print(str(i)+' / '+str(len(data)))
        # assign fields
        sent_id = sent['sent_id']
        doc_id = sent['sent_id'].split('-')[0] + '-' + sent['sent_id'].split('-')[1]
        text = sent['text']
        tokens = ' '.join([x['word'] for x in sent['toks']])
        note = sent['note'] if 'note' in sent else DEFAULT_STR
        mwe_markup = sent['mwe']
        add_corp_sent()

        for words in [sent['swes'], sent['smwes'], sent['wmwes']]:
            for i in words:
                if words[i]['lexcat'] in ['P', 'PRON.POSS', 'POSS', 'PP', 'INF.P']:

                    adposition_name = get_adp(words[i]['lexlemma'], language_name)

                    tok_sem = words[i]  # token semantic features
                    tok_morph = sent['toks'][tok_sem['toknums'][0] - 1]  # token morphological/syntactic features
                    # used to check NoneType
                    govobj = tok_sem['heuristic_relation']
                    if adposition_name in ['in_this_day','to_eat','to_go']:
                        tok_sem['lexcat']='PP'
                        hasobj = False
                    elif adposition_name in ['in_hope_to', 'just_about', 'nothing_but', 'back_and_forth', 'up_and_run']:
                        tok_sem['lexcat'] = 'P'
                    hasobj = type(govobj['obj']) is int and not tok_sem['lexcat']=='PP'
                    hasgov = type(govobj['gov']) is int

                    # assign fields
                    token_indices = ' '.join([str(x) for x in tok_sem['toknums']])
                    if '?' in tok_sem['ss'] or '`' in tok_sem['ss']:
                        role_name = DEFAULT_STR
                        function_name = DEFAULT_STR
                        special = tok_sem['ss']
                    else:
                        role_name = tok_sem['ss'].replace('p.', '')
                        function_name = tok_sem['ss2'].replace('p.', '')
                        special = DEFAULT_STR
                    obj_case = 'Accusative' if not tok_sem['lexcat'] in ['PRON.POSS', 'POSS'] else 'Genitive'
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
                    adposition_id = ids.clean_adp(language_name, adposition_name)
                    construal_id = ids.clean_con(role_name, function_name, special)
                    usage_id = ids.clean_us(adposition_name, int(construal_id)) if not construal_id == '0' \
                        else '0'
                    gov_head_index = str(govobj['gov']) if hasgov else DEFAULT_STR
                    obj_head_index = str(govobj['obj']) if hasobj else DEFAULT_STR
                    mwe_subtokens = tok_sem['lexlemma']
                    main_subtoken_indices = main_indices(token_indices)
                    main_subtoken_string = main_string(mwe_subtokens, token_indices)
                    if int(construal_id)>0 and int(usage_id)>0 and int(adposition_id)>0:
                        add_ptoken()

                    morphtype = 'standalone_preposition' if not adposition_name == "'s" else 'suffix'
                    is_pp_idiom = '1' if tok_sem['lexcat'] == 'PP' else '0'
                    if hasobj:
                        adp_trans.add(adposition_name)
                    else:
                        adp_intrans.add(adposition_name)
                    if not (adposition_name,is_pp_idiom) in adposition_set:
                        adposition_json.append({
                            'adposition_name':adposition_name,
                            'language_name':language_name,
                            'morphtype':morphtype,
                            'obj_case':obj_case,
                            'is_pp_idiom':is_pp_idiom,
                        })
                        adposition_set.add((adposition_name,is_pp_idiom))
                    role_id = ids.clean_ss(role_name)
                    function_id = ids.clean_ss(function_name)
                    if not (role_name, function_name, special) in construal_set and ((int(role_id)>0 and int(function_id)>0) or special):
                        construal_json.append({
                                'role_name':role_name,
                                'function_name':function_name,
                                'special':special,
                                'role_id':role_id,
                                'function_id':function_id
                        })
                        construal_set.add( (role_name, function_name, special) )
                    if not (adposition_name, role_name, function_name) in usage_set and int(adposition_id)>0 and int(construal_id)>0:
                        usage_json.append({
                            'adposition_name':adposition_name,
                            'role_name':role_name,
                            'function_name': function_name,
                            'obj_case':obj_case,
                            'adposition_id': adposition_id,
                            'construal_id': construal_id
                        })
                        usage_set.add( (adposition_name, role_name, function_name) )
                    if not role_name in supersense_set:
                        supersense_json.append({
                            'supersense_name':role_name
                        })
                        supersense_set.add(role_name)
                    if not function_name in supersense_set:
                        supersense_json.append({
                            'supersense_name':function_name
                        })
                        supersense_set.add(function_name)
print(str(len(data))+' / '+str(len(data)))
construal_json.append({
    'role_name':' ',
    'function_name':' ',
    'special':'`$',
    'role_id':'0',
    'function_id':'0'
    })
construal_json.append({
    'role_name':' ',
    'function_name':' ',
    'special':'`i',
    'role_id':'0',
    'function_id':'0'
    })
construal_json.append({
    'role_name':' ',
    'function_name':' ',
    'special':'`d',
    'role_id':'0',
    'function_id':'0'
    })
construal_json.append({
    'role_name':' ',
    'function_name':' ',
    'special':'`c',
    'role_id':'0',
    'function_id':'0'
    })

if not os.path.exists(dir):
    os.makedirs(dir)

# output CorpusSentences
print('corpus_sentences.json')
file = os.path.join(dir,'corpus_sentences.json')
with open(file, 'w', encoding='utf8') as f:
    json.dump(corpus_sentences, f)

# output SupersenseRevisions
print('supersense_revisions.json')
file = os.path.join(dir,'supersense_revisions.json')
with open(file, 'w') as f:
    json.dump(supersense_json, f)

# output AdpositionRevisions
# calculate adposition transitivity
for i,a in enumerate(adposition_json):
    adp = a['adposition_name']
    trans = 'sometimes_transitive' if (adp in adp_trans and adp in adp_intrans) \
                            else 'always_transitive' if adp in adp_trans \
                            else 'always_intransitive'
    adposition_json[i]['transitivity'] = trans
print('adposition_revisions.json')
file = os.path.join(dir,'adposition_revisions.json')
with open(file, 'w') as f:
    json.dump(adposition_json, f)

# output Construals
file = os.path.join(dir,'construals.json')
if len(construal_json)>1:
    print('construals.json')
    with open(file, 'w') as f:
        json.dump(construal_json, f)
else:
    print('skipping construals.json')

# output UsageRevisions
file = os.path.join(dir,'usage_revisions.json')
if [u['adposition_name'] for u in usage_json if not u['adposition_name']=='at']:
    print('usage_revisions.json')
    with open(file, 'w') as f:
        json.dump(usage_json, f)
else:
    print('skipping usages.json')

# output PTokenAnnotations
file = os.path.join(dir,'ptoken_annotations.json')
if [p['adposition_name'] for p in ptoken_annotations if not p['adposition_name']=='at']:
    print('ptoken_annotations.json')
    with open(file, 'w', encoding='utf8') as f:
        json.dump(ptoken_annotations, f)
else:
    print('skipping ptoken_annotations.json')
