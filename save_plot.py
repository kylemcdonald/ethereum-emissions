import pandas as pd
from collections import defaultdict

class SavePlot:
    def __init__(self):
        self.data = defaultdict(defaultdict)

    def add(self, xs, ys, name):
        for x,y in zip(xs, ys):
            self.data[x][name] = y
    
    def write(self, fn):
        pd.DataFrame(self.data).T.to_csv(fn)