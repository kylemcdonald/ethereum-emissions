import re
import json
import pandas as pd
from block_index import decode_extra_data

class BlockClassifier:
    def __init__(self,
            extra_data_label_regex_fn='data/extra_data_label_regex.json',
            miner_labels_fn='data/mining-addresses.csv'):
        with open(extra_data_label_regex_fn) as f:
            regexes = json.load(f)
        self.extra_data_label_regex = [(re.compile(regex, re.IGNORECASE), label) for regex,label in regexes.items()]
        self.miner_labels = pd.read_csv(miner_labels_fn).set_index('address').to_dict()['miner']

    def classify_extra_data(self, extra_data):
        found_label = None
        decoded = decode_extra_data(extra_data)
        for regex, label in self.extra_data_label_regex:
            if regex.search(decoded):
                found_label = label
                break
        return found_label

    def classify_miner(self, miner):
        miner = '0x' + miner.hex()
        if miner in self.miner_labels:
            return self.miner_labels[miner]

    def classify_block(self, extra_data, miner):
        label = self.classify_extra_data(extra_data)
        if label is None:
            label = self.classify_miner(miner)
        if label is None:
            return 'unknown'
        return label