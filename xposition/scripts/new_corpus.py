import json
import sys

from tqdm import tqdm
from wiki.plugins.metadata import models as ms
from wiki.models import Article


DEFAULT_STR = ' '

FILE = 'streusle.go.notes.json'

LANGUAGE = 'English'
CORPUS = 'STREUSLE'
VERSION = '4.3'
ORTHOGRAPHY = DEFAULT_STR



class Data:
    def __init__(self, missing_ss_error=False, missing_con_error=False, missing_us_error=False, missing_adp_error=False,
                 save_ss=False, save_adp=False, save_con=False, save_us=False, save_sent=False, save_ptok=False):

        self.data_file = FILE
        self.corpus_sentences_header = ['corpus_name', 'corpus_version', 'sent_id', 'language_name', 'orthography', 'is_parallel', 'doc_id',
                                   'text', 'tokens', 'word_gloss', 'sent_gloss', 'note', 'mwe_markup']

        self.ptoken_header = ['token_indices', 'adposition_name', 'language_name', 'role_name', 'function_name', 'special', 'corpus_name',
                         'corpus_version', 'sent_id', 'obj_case', 'obj_head', 'gov_head', 'gov_obj_syntax', 'gov_head_index',
                         'obj_head_index', 'is_typo', 'is_abbr', 'adp_pos', 'gov_pos', 'obj_pos', 'gov_supersense',
                         'obj_supersense', 'is_gold', 'annotator_cluster', 'is_transitive', 'adposition_id', 'construal_id',
                         'usage_id', 'mwe_subtokens', 'main_subtoken_indices', 'main_subtoken_string']

        self.corpus_sentences = []
        self.ptoken_annotations = []
        self.construal_json = []
        self.adposition_json = []
        self.usage_json = []
        self.supersense_json = [{'supersense_name': 'Temporal'}, {'supersense_name': 'Configuration'}, {'supersense_name': 'Participant'}]
        # self.supersense_article_json = []
        # self.construal_article_json = []

        self.construal_set = set()
        self.adposition_set = set()
        self.usage_set = set()
        self.supersense_set = set()
        self.adp_trans = set()
        self.adp_intrans = set()

        # corpus sent
        self.corpus_name = CORPUS
        self.corpus_version = VERSION
        self.language_name = LANGUAGE
        self.sent_id = '0'
        self.orthography = ORTHOGRAPHY
        self.doc_id = '0'
        self.text = DEFAULT_STR
        self.tokens = DEFAULT_STR
        self.word_gloss = DEFAULT_STR
        self.sent_gloss = DEFAULT_STR
        self.note = DEFAULT_STR
        self.mwe_markup = DEFAULT_STR

        # ptoken
        self.token_indices = DEFAULT_STR
        self.adposition_name = DEFAULT_STR
        self.role_name = DEFAULT_STR
        self.function_name = DEFAULT_STR
        self.special = DEFAULT_STR
        self.obj_case = DEFAULT_STR
        self.obj_head = DEFAULT_STR
        self.gov_head = DEFAULT_STR
        self.gov_obj_syntax = DEFAULT_STR
        self.adp_pos = DEFAULT_STR
        self.gov_pos = DEFAULT_STR
        self.obj_pos = DEFAULT_STR
        self.gov_supersense = DEFAULT_STR
        self.obj_supersense = DEFAULT_STR
        self.is_gold = '1'
        self.annotator_cluster = DEFAULT_STR
        self.is_transitive = '1'
        self.adposition_id = '0'
        self.construal_id = '0'
        self.usage_id = '0'
        self.gov_head_index = DEFAULT_STR
        self.obj_head_index = DEFAULT_STR
        self.is_typo = '0'
        self.is_abbr = '0'
        self.mwe_subtokens = DEFAULT_STR
        self.main_subtoken_indices = DEFAULT_STR
        self.main_subtoken_string = DEFAULT_STR

        self.missing_ss_error = missing_ss_error
        self.missing_con_error = missing_con_error
        self.missing_us_error = missing_us_error
        self.missing_adp_error = missing_adp_error

        self.save_ss = save_ss
        self.save_adp = save_adp
        self.save_con = save_con
        self.save_us = save_us
        self.save_sent = save_sent
        self.save_ptok = save_ptok

    def get(self, name):
        return getattr(self, name)

    def load_data(self, file):
        query = DatabaseQuery()

        with open(file, encoding='utf8') as f:
            sentences = json.load(f)
        for i, sent in enumerate(tqdm(sentences, file=sys.stdout)):
            # if i % 500 == 0:
            #     print(str(i) + ' / ' + str(len(sentences)))
            # assign fields
            self.sent_id = sent['sent_id']
            if self.save_sent:
                self.doc_id, sentnum = sent['sent_id'].rsplit('-',1)
                self.text = sent['text']
                self.tokens = ' '.join([x['word'] for x in sent['toks']])
                self.note = sent['note'] if 'note' in sent else DEFAULT_STR
                self.mwe_markup = sent['mwe']
                self.add_corp_sent()

            for words in [sent['swes'], sent['smwes'], sent['wmwes']]:
                for i in words:
                    if words[i]['lexcat'] in ['P', 'PRON.POSS', 'POSS', 'PP', 'INF.P']:

                        tok_sem = words[i]  # token semantic features
                        tok_morph = sent['toks'][tok_sem['toknums'][0] - 1]  # token morphological/syntactic features

                        if self.save_adp or self.save_us or self.save_ptok:
                            self.adposition_name = query.get_adp(words[i]['lexlemma'], self.language_name)

                            govobj = tok_sem['heuristic_relation']  # used to check NoneType
                            if self.adposition_name in ['in_this_day', 'to_eat', 'to_go']:
                                tok_sem['lexcat'] = 'PP'
                            elif self.adposition_name in ['in_hope_to', 'just_about', 'nothing_but', 'back_and_forth', 'up_and_run']:
                                tok_sem['lexcat'] = 'P'
                            hasobj = type(govobj['obj']) is int and not tok_sem['lexcat'] == 'PP'
                            hasgov = type(govobj['gov']) is int

                        if not tok_sem['toknums']:
                            raise Exception(f'No toknums: {self.sent_id}')

                        # assign fields
                        self.token_indices = ' '.join([str(x) for x in tok_sem['toknums']])
                        if '?' in tok_sem['ss'] or '`' in tok_sem['ss']:
                            self.role_name = DEFAULT_STR
                            self.function_name = DEFAULT_STR
                            self.special = tok_sem['ss']
                        else:
                            self.role_name = tok_sem['ss'].replace('p.', '')
                            self.function_name = tok_sem['ss2'].replace('p.', '')
                            self.special = DEFAULT_STR
                        self.obj_case = 'Accusative' if not tok_sem['lexcat'] in ['PRON.POSS', 'POSS'] else 'Genitive'
                        self.adposition_id = query.adposition(self.language_name, self.adposition_name, self.sent_id, raise_error=self.missing_adp_error)
                        self.construal_id = query.construal(self.role_name, self.function_name, self.special, self.sent_id, raise_error=self.missing_con_error)
                        self.usage_id = query.usage(int(self.adposition_id), int(self.construal_id), self, self.sent_id, raise_error=self.missing_us_error)

                        if self.save_ptok and int(self.construal_id) > 0 and int(self.usage_id) > 0 and int(self.adposition_id) > 0:
                            self.obj_head = govobj['objlemma'] if hasobj else DEFAULT_STR
                            self.gov_head = govobj['govlemma'] if hasgov else DEFAULT_STR
                            self.gov_obj_syntax = govobj['config']
                            self.adp_pos = tok_morph['upos']
                            self.gov_pos = sent['toks'][govobj['gov'] - 1]['upos'] if hasgov else DEFAULT_STR
                            self.obj_pos = sent['toks'][govobj['obj'] - 1]['upos'] if hasobj else DEFAULT_STR
                            self.gov_supersense = self.get_ss(sent, govobj['gov']) if hasgov else DEFAULT_STR
                            self.obj_supersense = self.get_ss(sent, govobj['obj']) if hasobj else DEFAULT_STR
                            self.annotator_cluster = tok_sem['annotator_cluster'] if 'annotator_cluster' in tok_sem else DEFAULT_STR
                            self.is_transitive = '1' if hasobj else '0'
                            self.gov_head_index = str(govobj['gov']) if hasgov else DEFAULT_STR
                            self.obj_head_index = str(govobj['obj']) if hasobj else DEFAULT_STR
                            self.mwe_subtokens = tok_sem['lexlemma']
                            self.main_subtoken_indices = self.main_indices(self.token_indices)
                            self.main_subtoken_string = self.main_string(self.mwe_subtokens, self.token_indices)
                            toks = [sent['toks'][j - 1] for j in tok_sem['toknums']]
                            feats = []
                            for t in toks:
                                if isinstance(t['feats'], str):
                                    feats.extend(t['feats'].split('|'))
                            self.is_typo = '1' if 'Typo=Yes' in feats else '0'
                            self.is_abbr = '1' if 'Abbr=Yes' in feats else '0'
                            self.add_ptoken()
                        # else:
                        #     print(adposition_name, adposition_id)
                        #     print(role_name, function_name, special, construal_id)
                        #     print(adposition_name+':', role_name, function_name, special, usage_id)

                        self.is_pp_idiom = '1' if tok_sem['lexcat'] == 'PP' else '0'
                        if self.save_adp and not (self.adposition_name, self.is_pp_idiom) in self.adposition_set:
                            self.morphtype = 'standalone_preposition' if not self.adposition_name == "'s" else 'suffix'
                            if hasobj:
                                self.adp_trans.add(self.adposition_name)
                            else:
                                self.adp_intrans.add(self.adposition_name)
                            self.adposition_json.append({
                                'adposition_name': self.adposition_name,
                                'language_name': self.language_name,
                                'morphtype': self.morphtype,
                                'obj_case': self.obj_case,
                                'is_pp_idiom': self.is_pp_idiom,
                            })
                            self.adposition_set.add((self.adposition_name, self.is_pp_idiom))
                        role_id = query.supersense(self.role_name, self.sent_id, raise_error=self.missing_ss_error)
                        function_id = query.supersense(self.function_name, self.sent_id, raise_error=self.missing_ss_error)
                        if self.save_con and not (self.role_name, self.function_name, self.special) in self.construal_set and (
                            (int(role_id) > 0 and int(function_id) > 0) or self.special):
                            self.construal_json.append({
                                'role_name': self.role_name,
                                'function_name': self.function_name,
                                'special': self.special,
                                'role_id': role_id,
                                'function_id': function_id
                            })
                            self.construal_set.add((self.role_name, self.function_name, self.special))
                        if self.save_us and not (self.adposition_name, self.role_name, self.function_name, self.special) in self.usage_set and \
                            int(self.adposition_id) > 0 and int(self.construal_id) > 0:
                            self.usage_json.append({
                                'adposition_name': self.adposition_name,
                                'role_name': self.role_name,
                                'function_name': self.function_name,
                                'obj_case': self.obj_case,
                                'adposition_id': self.adposition_id,
                                'construal_id': self.construal_id
                            })
                            self.usage_set.add((self.adposition_name, self.role_name, self.function_name, self.special))
                        if self.save_ss and self.role_name.strip() and not self.role_name in self.supersense_set:
                            self.supersense_json.append({
                                'supersense_name': self.role_name
                            })
                            self.supersense_set.add(self.role_name)
                        if self.save_ss and self.function_name.strip() and not self.function_name in self.supersense_set:
                            self.supersense_json.append({
                                'supersense_name': self.function_name
                            })
                            self.supersense_set.add(self.function_name)
        # print(str(len(sentences)) + ' / ' + str(len(sentences)))
        if self.save_con:
            self.construal_json.append({
                'role_name': ' ',
                'function_name': ' ',
                'special': '`$',
                'role_id': '0',
                'function_id': '0'
            })
            self.construal_json.append({
                'role_name': ' ',
                'function_name': ' ',
                'special': '`i',
                'role_id': '0',
                'function_id': '0'
            })
            self.construal_json.append({
                'role_name': ' ',
                'function_name': ' ',
                'special': '`d',
                'role_id': '0',
                'function_id': '0'
            })
            self.construal_json.append({
                'role_name': ' ',
                'function_name': ' ',
                'special': '`c',
                'role_id': '0',
                'function_id': '0'
            })
            self.construal_set.update({(' ',' ','`$'),
                                       (' ',' ','`i'),
                                       (' ',' ','`d'),
                                       (' ',' ','`c'),})

        # for role_name,function_name,special in self.construal_set:
        #     article_slug = f'{role_name}--{function_name}' if not special.strip() else f'{special}'
        #     article = query.article(article_slug)
        #     if article is None:
        #         self.construal_article_json.append(
        #             {'content': ' ',
        #              'title': article_slug,
        #              'article_id': '0'}
        #         )
        # for role_name in self.supersense_set:
        #     article = query.article(role_name)
        #     if article is None:
        #         self.supersense_article_json.append(
        #             {'content': ' ',
        #              'title': role_name,
        #              'article_id': '0'}
        #         )

    def add_corp_sent(self):
        x = {}
        for s in self.corpus_sentences_header:
            x[s] = self.get(s)
        self.corpus_sentences.append(x)

    def add_ptoken(self):
        x = {}
        for s in self.ptoken_header:
            x[s] = self.get(s)
        self.ptoken_annotations.append(x)

    def get_ss(self, sent, n):
        supersense = DEFAULT_STR
        for ws in [sent['swes'], sent['smwes']]:
            for tok in ws:
                if n in ws[tok]['toknums']:
                    supersense = ws[tok]['ss']
        if supersense == None:
            supersense = DEFAULT_STR
        return supersense


    def main_indices(self, token_indices=''):
        x = []
        for i in token_indices.split():
            # only add direct successor
            if not x or int(i) == int(x[-1]) + 1:
                x.append(i)
            else:
                break
        return ' '.join(x)

    def main_string(self, mwe_subtokens='', token_indices=''):
        x = self.main_indices(token_indices).split()
        return ' '.join(mwe_subtokens.split()[:len(x)])


class DatabaseQuery:
    adp_memo = {}
    ss_memo = {}
    con_memo = {}
    us_memo = {}
    article_memo = {}

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
            self.us_memo[(u.current_revision.metadatarevision.usagerevision.adposition.pk,
                     u.current_revision.metadatarevision.usagerevision.construal.pk)] \
                = str(u.pk)

        for a in Article.objects.all():
            self.article_memo[str(a.urlpath_set.all().first())[:-1]] = a.pk


    def get_adp(self, s, lang):
        adp = ms.Adposition.normalize_adp(cls=ms.Adposition,
                                          adp=s,
                                          language_name=lang)
        adp = adp or s
        adp = adp.replace(' ', '_')
        if adp in ['he', 'it', "it's", 'she', 'there', 'they', 'thier', 'ur', 'we', 'you']:
            adp = "'s"
        return adp

    def article(self, article_name):
        if article_name in self.article_memo:
            return self.article_memo[article_name]
        else:
            return None

    def adposition(self, language_name, adposition_name, sent_id, raise_error=False):
        if (adposition_name,language_name) in self.adp_memo:
            return self.adp_memo[(adposition_name,language_name)]
        else:
            if raise_error:
                raise Exception(f'Adposition Missing: {sent_id} {language_name} {adposition_name}')
            return '0'

    def construal(self, role_name, function_name, special, sent_id, raise_error=False):
        if (role_name, function_name, special) in self.con_memo:
            return self.con_memo[(role_name, function_name, special)]
        else:
            if raise_error:
                raise Exception(f'Construal Missing: {sent_id} {role_name} {function_name} {special}')
            return '0'

    def usage(self, adposition_id, construal_id, data, sent_id, raise_error=False):
        if int(adposition_id) == 0 or int(construal_id) == 0:
            if raise_error:
                raise Exception(f'Usage Missing: {sent_id} {data.adposition_name} {data.role_name} '
                                f'{data.function_name} {data.special} {adposition_id} {construal_id}')
            return '0'
        if (adposition_id, construal_id) in self.us_memo:
            return self.us_memo[(adposition_id, construal_id)]
        else:
            if raise_error:
                raise Exception(f'Usage Missing: {sent_id} {data.adposition_name} {data.role_name} '
                                f'{data.function_name} {data.special} {adposition_id} {construal_id}')
            return '0'

    def supersense(self, name, sent_id, raise_error=False):
        if not name.strip():
            return '0'
        if name in self.ss_memo:
            return self.ss_memo[name]
        else:
            if raise_error:
                raise Exception(f'Supersense Missing: {sent_id} {name}')
            return '0'
