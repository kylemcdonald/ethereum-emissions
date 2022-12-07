import datetime
from dateutil import tz
from collections import defaultdict

from block_index import BlockIndex
from block_classifier import BlockClassifier

from tqdm import tqdm
import pandas as pd
import numpy as np

using_metadata_snapshot = True
index = BlockIndex(read_only=True)
classifier = BlockClassifier()

block_labels = defaultdict(lambda: defaultdict(int))

total = index.latest_block() - 1
for block in tqdm(index.list_blocks(skip_genesis=True), total=total):
    dt = block.get_datetime()
    if using_metadata_snapshot:
        # metadata snapshot is in los angeles timezone
        dt.replace(tzinfo=tz.gettz('America/Los_Angeles'))
    else:
        # any data from a local copy will be in the local timezone
        dt.replace(tzinfo=tz.tzlocal())
    dt = dt.astimezone(tz.tzutc()) # convert from database time to UTC time
    date = dt.date()

    # first, try to label the block based on the extra data
    label = classifier.classify_extra_data(block.extra_data)
    if label is not None:
        label = 'extraData:' + label
    else:
        # if that doesn't work, label it based on the pool
        label = classifier.classify_miner(block.miner)
        if label is not None:
            label = 'pool:' + label
    # if neither work, call it 'unknown'
    if label is None:
        label = 'unknown'
    block_labels[date][label] += 1

df = pd.DataFrame(block_labels).T.sort_index()
df.index.name = 'Date'
df.to_csv('output/block-labels.csv', float_format='%.0f')