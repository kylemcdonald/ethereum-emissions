import os
import socket
import itertools
import json

class FastWeb3:
    def __init__(self, ipc_path='~/.ethereum/geth.ipc', timeout=1):
        ipc_path = os.path.expanduser(ipc_path)
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.connect(ipc_path)
        self.sock.settimeout(timeout)
        self.request_counter = itertools.count()
        
    def make_request(self, method, params, id=None):
        if id is None:
            id = next(self.request_counter)
        return f'{{"jsonrpc":"2.0","method":"{method}","params":{params},"id":{id}}}'.encode('ascii')
        
    def batch_receive_response(self, total):
        raw_response = b''
        remaining_timeouts = 5
        while total > 0:
            try:
                chunk = self.sock.recv(4096)
                raw_response += chunk
                total -= chunk.count(b'\n')
            except socket.timeout:
                remaining_timeouts -= 1
                if remaining_timeouts == 0:
                    raise
        responses = raw_response.split(b'\n')[:-1]
        data = [json.loads(e) for e in responses]
        return data
    
    def get_block_by_number(self, block_number):
        return self.batch_get_block_by_number(block_number)[0]
        
    def batch_get_block_by_number(self, block_numbers):
        for block_number in block_numbers:
            params = f'["{hex(block_number)}",false]'
            request = self.make_request('eth_getBlockByNumber', params, id=block_number)
            self.sock.sendall(request)
        return self.batch_receive_response(len(block_numbers))
    
    def get_block_by_hash(self, block_hash):
        return self.batch_get_block_by_hash(block_hash)[0]
    
    def batch_get_block_by_hash(self, block_hashes):
        for block_hash in block_hashes:
            params = f'["{block_hash}",false]'
            request = self.make_request('eth_getBlockByHash', params)
            self.sock.sendall(request)
        return self.batch_receive_response(len(block_hashes))
    
    def get_latest_block(self):
        params = f'["latest",false]'
        request = self.make_request('eth_getBlockByNumber', params)
        self.sock.sendall(request)
        return self.batch_receive_response(1)[0]
        
    def get_latest_block_number(self):
        block_hash = self.get_latest_block()['result']['hash']
        block_number = self.get_block_by_hash([block_hash])['result']['number']
        return int(block_number, 16)

    def __del__(self):
        self.sock.close()