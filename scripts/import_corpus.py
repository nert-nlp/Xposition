import tablib
from import_export import resources
from wiki.plugins.metadeta import models


file = '?????'


corpus_sent_resource = resources.modelresource_factory(model=CorpusSentence)()
# ptoken_resource = resources.modelresource_factory(model=PTokenAnnotation)()

data = tablib.Dataset()
data.tsv = open(file).read()

result = corpus_sent_resource.import_data(data, dry_run=True)

print(result.has_errors())
# run this line if there are no errors
#result = book_resource.import_data(data, dry_run=False)