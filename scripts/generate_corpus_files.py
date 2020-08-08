import csv
import os

from unidecode import unidecode

os.chdir('../scripts')
from new_corpus import Data


class TSV_Writer:

    @staticmethod
    def _normalize(k, s):
        line = str(s)
        line = unidecode(line)
        return line

    @staticmethod
    def write_tsv(json_data, file):
        keys = list(sorted({k for row in json_data for k in row}))
        with open(file, 'w+', encoding='utf8', newline='') as f:
            tsv_writer = csv.writer(f, delimiter='\t')
            tsv_writer.writerow([k for k in keys])
            for j, row in enumerate(json_data):
                tsv_writer.writerow([TSV_Writer._normalize(k, row[k]) if k in row else '' for k in keys])


def main():

    data = Data(save_sent=True, save_ptok=True, missing_ss_error=True, missing_con_error=True, missing_adp_error=True, missing_us_error=True)

    output_dir = f'{data.corpus_name}{data.corpus_version}_files'

    data.load_data(data.data_file)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # output CorpusSentences
    print('corpus_sentences.json', len(data.corpus_sentences))
    file = os.path.join(output_dir, 'corpus_sentences.tsv')
    TSV_Writer.write_tsv(data.corpus_sentences, file)

    # output PTokenAnnotations
    # split ptokens json into multiple files of a particular size
    PER_FILE = 1500
    if data.ptoken_annotations:
        for i in range(int(len(data.ptoken_annotations) / PER_FILE)):
            file = os.path.join(output_dir, f'ptoken_annotations{i}.tsv')
            print(file, i * PER_FILE, '-', (i + 1) * PER_FILE - 1)
            TSV_Writer.write_tsv(data.ptoken_annotations[i * PER_FILE:(i + 1) * PER_FILE], file)

        i = int(len(data.ptoken_annotations) / PER_FILE)
        file = os.path.join(output_dir, f'ptoken_annotations{i}.tsv')
        print(file, i * PER_FILE, '-', len(data.ptoken_annotations) - 1)
        TSV_Writer.write_tsv(data.ptoken_annotations[i * PER_FILE:], file)

    else:
        raise Exception('No PTokenAnnotations found. Please make sure all Usages and CorpusSentences have been imported or exist.')


    unique_sent_and_tokens = set()
    for p in data.ptoken_annotations:
        sent_and_tokens = p['sent_id']+' '+str(p['token_indices'])
        if sent_and_tokens in unique_sent_and_tokens:
            sent_id = p['sent_id']
            token_indices = str(p['token_indices'])
            raise Exception(f'Unique Constraint Failure: sent_id "{sent_id}" and token_indices "{token_indices}"')
        else:
            unique_sent_and_tokens.add(sent_and_tokens)



if __name__ == '__main__':
    main()
