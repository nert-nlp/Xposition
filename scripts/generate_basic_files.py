import os, json

os.chdir('../scripts')
from new_corpus import Data


def main():

    data = Data(save_adp=True, save_ss=True)

    output_dir = f'{data.corpus_name}{data.corpus_version}_files'

    data.load_data(data.data_file)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # output SupersenseRevisions
    print('supersense_revisions.json', len(data.supersense_json))
    file = os.path.join(output_dir, 'supersense_revisions.json')
    with open(file, 'w+', encoding='utf8') as f:
        json.dump(data.supersense_json, f)

    # output AdpositionRevisions
    # calculate adposition transitivity
    for i, a in enumerate(data.adposition_json):
        adp = a['adposition_name']
        trans = 'sometimes_transitive' if (adp in data.adp_trans and adp in data.adp_intrans) \
            else 'always_transitive' if adp in data.adp_trans \
            else 'always_intransitive'
        data.adposition_json[i]['transitivity'] = trans
    print('adposition_revisions.json', len(data.adposition_json))
    file = os.path.join(output_dir, 'adposition_revisions.json')
    with open(file, 'w+', encoding='utf8') as f:
        json.dump(data.adposition_json, f)


if __name__=='__main__':
    main()
