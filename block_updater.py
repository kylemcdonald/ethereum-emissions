from utils.itertools import chunks
import time

from fast_web3 import FastWeb3
from block_index import BlockIndex

chunk_size = 100
web3 = FastWeb3()
index = BlockIndex()

latest_block_number = web3.get_latest_block_number()
end_block = latest_block_number
indexed_block = index.latest_block()
start_block = 0 if indexed_block is None else indexed_block
n = end_block - start_block
start_time = time.time()
last_diff = 0
update_rate = 60

print(f'syncing #{start_block} to #{end_block}')
for block_numbers in chunks(range(start_block, latest_block_number), chunk_size):
    block_number = block_numbers[0]
    duration = time.time() - start_time
    diff = duration % update_rate
    if diff < last_diff:
        remaining_blocks = end_block - block_number
        processed_blocks = block_number - start_block
        remaining_duration = (remaining_blocks / processed_blocks) * duration
        print(f'#{block_number} {remaining_duration:.1f}s')
    last_diff = diff

    responses = web3.batch_get_block_by_number(block_numbers)
    index.insert_blocks(responses)