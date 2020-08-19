import json
import os

os.chdir('scripts')
from .new_corpus import Data



def main():

    data = Data(missing_ss_error=True, missing_con_error=True, missing_adp_error=True, save_us=True)

    output_dir = f'{data.corpus_name}{data.corpus_version}_files'

    data.load_data(data.data_file)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # output UsageRevisions
    file = os.path.join(output_dir, 'usage_revisions.json')
    if data.usage_json:
        print('usage_revisions.json', len(data.usage_json))
        with open(file, 'w+', encoding='utf8') as f:
            json.dump(data.usage_json, f)
    else:
        raise Exception('No Usages found. Please make sure all Adpositions and Construals have been imported or exist.')



if __name__=='__main__':
    main()
