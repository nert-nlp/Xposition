import json
import os

os.chdir('scripts')
from .new_corpus import Data

def main():
    data = Data(missing_ss_error=True, save_con=True)

    output_dir = f'{data.corpus_name}{data.corpus_version}_files'

    data.load_data(data.data_file)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # output Construals
    file = os.path.join(output_dir, 'construals.json')
    if len(data.construal_json) > 1:
        print('construals.json', len(data.construal_json))
        with open(file, 'w+', encoding='utf8') as f:
            json.dump(data.construal_json, f)
    else:
        raise Exception('No Construals found. Please make sure all Supersenses have been imported or exist.')


if __name__ == '__main__':
    main()
