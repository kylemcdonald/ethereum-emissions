from block_index import BlockIndex
from block_index import hash0x_to_bytes
from tqdm import tqdm
import codecs
from collections import Counter
import json

index = BlockIndex(read_only=True)
total = index.latest_block() - 1
pairs = [(block.miner, e.extra_data) for e in tqdm(index.list_blocks(skip_genesis=True))]

def decode_extra_data(e):
    try:
        return e.decode('utf-8')
    except:
        return repr(e)[2:-1]

# ignore edges with this number of instances of fewer
cutoff = 1

with open('output/top-miners.dot', 'w') as f:
    f.write('graph {\n')
    common = Counter(pairs).most_common()
    for (miner,extra_data), count in common:
        # first 4 values are enough to uniquely identify all miners
        if count == cutoff:
            continue
        miner = codecs.encode(miner, 'hex').decode('utf8')
        extra_data = decode_extra_data(extra_data)
        if extra_data == "":
            extra_data = "null"
        f.write(f'  {miner[:4]} -- "{extra_data}" [weight={count}];\n')
    f.write('}\n')