import json
import os

from ..scripts.generate_basic_files import Data


def main():
    dir = 'json'

    file = 'streusle.go.notes.json'

    data = Data(missing_ss_error=True, missing_con_error=True, missing_adp_error=True, save_us=True)

    data.load_data(file)
    if not os.path.exists(dir):
        os.makedirs(dir)

    # output UsageRevisions
    file = os.path.join(dir, 'usage_revisions.json')
    if data.usage_json:
        print('usage_revisions.json', len(data.usage_json))
        with open(file, 'w') as f:
            json.dump(data.usage_json, f)
    else:
        raise Exception('No Usages found. Please make sure all Adpositions and Construals have been imported or exist.')



if __name__=='__main__':
    main()
