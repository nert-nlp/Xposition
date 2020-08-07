import csv
import json
import os

from unidecode import unidecode

from ..scripts.generate_basic_files import Data


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
    dir = 'json'

    file = 'streusle.go.notes.json'

    data = Data(save_sent=True, save_ptok=True, missing_ss_error=True, missing_con_error=True, missing_adp_error=True, missing_us_error=True)

    data.load_data(file)
    if not os.path.exists(dir):
        os.makedirs(dir)

    # output CorpusSentences
    print('corpus_sentences.json', len(data.corpus_sentences))
    file = os.path.join(dir, 'corpus_sentences.tsv')
    TSV_Writer.write_tsv(data.corpus_sentences, file)

    # output PTokenAnnotations
    # split ptokens json into multiple files of a particular size
    PER_FILE = 1500
    if data.ptoken_annotations:
        for i in range(int(len(data.ptoken_annotations) / PER_FILE)):
            file = os.path.join(dir, f'ptoken_annotations{i}.tsv')
            print(file, i * PER_FILE, '-', (i + 1) * PER_FILE - 1)
            TSV_Writer.write_tsv(data.ptoken_annotations[i * PER_FILE:(i + 1) * PER_FILE], file)

        i = int(len(data.ptoken_annotations) / PER_FILE)
        file = os.path.join(dir, f'ptoken_annotations{i}.tsv')
        print(file, i * PER_FILE, '-', len(data.ptoken_annotations) - 1)
        TSV_Writer.write_tsv(data.ptoken_annotations[i * PER_FILE:], file)

    else:
        raise Exception('No PTokenAnnotations found. Please make sure all Usages and CorpusSentences have been imported or exist.')


if __name__ == '__main__':
    main()
