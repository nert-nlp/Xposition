import json
import os

from ..scripts.generate_basic_files import Data


def main():
    dir = 'json'

    file = 'streusle.go.notes.json'

    data = Data(missing_ss_error=True, save_con=True)

    data.load_data(file)
    if not os.path.exists(dir):
        os.makedirs(dir)

    # output Construals
    file = os.path.join(dir, 'construals.json')
    if len(data.construal_json) > 1:
        print('construals.json', len(data.construal_json))
        with open(file, 'w') as f:
            json.dump(data.construal_json, f)
    else:
        raise Exception('No Construals found. Please make sure all Supersenses have been imported or exist.')


if __name__ == '__main__':
    main()
