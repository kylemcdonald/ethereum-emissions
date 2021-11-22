import json
import os

class Results:
    def __init__(self, fn='cache/results.json'):
        self.fn = fn
        try:
            with open(fn) as f:
                self.data = json.load(f)
        except:
            self.data = {}

    def write(self):
        with open(self.fn, 'w') as f:
            json.dump(self.data, f)

    def __setitem__(self, key, value):
        self.data[key] = str(value)

    def __getitem__(self, key):
        return self.data[key]

    def __str__(self):
        return '\n'.join([f'{k}={v}' for k,v in sorted(self.data.items())])

if __name__ == '__main__':
    results = Results()
    print(results)