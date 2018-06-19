import tablib
from import_export import resources
from wiki.plugins.metadeta import models

cs_file = 'corpus_sents.tsv'
ptok_file = 'ptokens.tsv'

class CorpusSentenceResource(resources.ModelResource):
    corpus = fields.Field(
        column_name='corpus_name',
        attribute='corpus',
        widget=ForeignKeyWidget(Corpus, 'name'))

    language = fields.Field(
        column_name='language_name',
        attribute='language',
        widget=ForeignKeyWidget(Language, 'name'))


    class Meta:
        fields = ('corpus', 'sent_id', 'language', 'orthography', 'is_parallel', 'doc_id',
                  'text', 'tokens', 'word_gloss', 'sent_gloss', 'note', 'mwe_markup')


class PTokenAnnotationResource(resources.ModelResource):
    corpus = fields.Field(
        column_name='corpus_name',
        attribute='corpus',
        widget=ForeignKeyWidget(Corpus, 'name'))

    adposition = fields.Field(
        column_name='adposition_name',
        attribute='adposition',
        widget=ForeignKeyWidget(Adposition, 'name'))

    construal = fields.Field(
        column_name='construal_name',
        attribute='construal',
        widget=ForeignKeyWidget(Construal, 'name'))

    sentence = fields.Field(
        column_name='sent_id',
        attribute='sentence',
        widget=ForeignKeyWidget(CorpusSentence, 'sent_id'))

    # usage = fields.Field(
    #     column_name='construal',
    #     attribute='usage',
    #     widget=ForeignKeyWidget(Usage, 'usage'))

    class Meta:
        fields = ('token_indices', 'adposition', 'construal', 'corpus', 'sentence',
                 'obj_case', 'obj_head', 'gov_head', 'gov_obj_syntax', 'adp_pos', 'gov_pos', 'obj_pos', 'gov_supersense',
                 'obj_supersense', 'is_gold', 'annotator_cluster')
        # fields = ('token_indices', 'adposition', 'construal', 'usage', 'corpus', 'sentence',
        #           'obj_case', 'obj_head', 'gov_head', 'gov_obj_syntax', 'adp_pos', 'gov_pos', 'obj_pos',
        #           'gov_supersense',
        #           'obj_supersense', 'is_gold', 'annotator_cluster')


corpus_sent_resource = CorpusSentenceResource()
ptoken_resource = PTokenAnnotationResource()

data = tablib.Dataset()
data.tsv = open(cs_file).read()

result = corpus_sent_resource.import_data(data, dry_run=True)

print(result.has_errors())

data = tablib.Dataset()
data.tsv = open(ptok_file).read()

result = ptoken_resource.import_data(data, dry_run=True)

print(result.has_errors())
# run this line if there are no errors
# result = book_resource.import_data(data, dry_run=False)
