import sqlite3
import datetime

def hash0x_to_bytes(hash0x):
    return bytearray.fromhex(hash0x[2:])

def build_rows(responses):
    for response in responses:
        block_number = response['id']
        block = response['result']
        yield (
            block_number,
            int(block['timestamp'], 16),
            hash0x_to_bytes(block['miner']),
            hash0x_to_bytes(block['extraData']))

def decode_extra_data(e):
    try:
        return e.decode('utf-8')
    except:
        return e.decode('latin-1')

class Block:
    def __init__(self, block_number, timestamp, miner, extra_data):
        self.block_number = block_number
        self.timestamp = timestamp
        self.miner = miner
        self.extra_data = extra_data

    def __repr__(self):
        return str(self.block_number)

    def extra_data_decoded(self):
        return decode_extra_data(self.extra_data)

    def get_datetime(self):
        return datetime.datetime.fromtimestamp(self.timestamp)

class BlockIndex:
    def __init__(self, db_file='extra_data.sqlite3', read_only=False):
        flags = '?mode=ro' if read_only else ''
        self.db = sqlite3.connect(f'file:{db_file}{flags}', uri=True)
        # self.db.execute('PRAGMA journal_mode=wal')
        cmd = 'CREATE TABLE IF NOT EXISTS extra_data \
            (block_number INTEGER PRIMARY KEY, \
            timestamp INTEGER, \
            miner BLOB, \
            extra_data BLOB)'
        self.db.execute(cmd)
        
    def __del__(self):
        self.db.close()
        
    def execute(self, query):
        return self.db.cursor().execute(query)

    def list_field(self, field, ordered=False):
        query = f'SELECT {field} FROM extra_data'
        for row in self.execute(query):
            yield row[0]

    def list_field_unique(self, field):
        query = f'SELECT DISTINCT {field} FROM extra_data'
        for row in self.execute(query):
            yield row[0]
    
    def insert_blocks(self, responses):
        query = f'INSERT OR REPLACE INTO extra_data VALUES (?, ?, ?, ?)'
        self.db.cursor().executemany(query, build_rows(responses))
        self.db.commit()
    
    def latest_block(self):
        query = 'SELECT MAX(block_number) FROM extra_data'
        return self.execute(query).fetchone()[0]

    def list_blocks(self, skip_genesis=False):
        query = f'SELECT * FROM extra_data ORDER BY block_number ASC'
        if skip_genesis:
            query += ' LIMIT -1 OFFSET 1'
        for row in self.execute(query):
            yield Block(*row)