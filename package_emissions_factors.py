import datetime
from results import Results
from block_classifier import BlockClassifier
from emissions_utils import read_csv_date, normalize_row_to_one, combine_and_rename
import numpy as np
import matplotlib.pyplot as plt
plt.rcParams['font.size'] = 20

def draw_ratios(df, legend=False, legend_n=8):
    dates = df.index.values
    labels = df.columns.values
    data = df.values.T
    indices = np.argsort(data.sum(1))[::-1]
    fig = plt.figure(figsize=(20,5), facecolor='white')
    plt.stackplot(dates, 100*data[indices], lw=0, labels=[labels[i] for i in indices])
    plt.xlim(dates[0], dates[-1])
    if data.max() == 1:
        plt.ylim(0,100)
    if legend:
        n = len(labels)
        plt.legend(ncol=min(n,legend_n),
                   loc='upper center',
                   bbox_to_anchor=(0.5, -0.1))
    plt.yticks([])
    return fig

# collapse groups and collect data for stackplot
groups = {
    'Asia': ['asia', 'singapore', 'taiwan', 'seoul'],
    'China': ['china'],
    'Europe': ['europe', 'europe-west', 'europe-north', 'russia', 'ukraine'],
    'USA': ['us', 'us-west', 'us-east'],
    'Unknown': ['unknown']
}

region_totals = read_csv_date('output/region-totals.csv')
region_totals_grouped = combine_and_rename(region_totals, groups)
region_totals_grouped.to_csv('output/region-totals-grouped.csv', float_format='%.0f')
region_pct_grouped = normalize_row_to_one(region_totals_grouped).sort_index()

# draw and save stackplot
fig = draw_ratios(region_pct_grouped, legend=True)
ban1 = datetime.datetime(2021,5,21).date()
ban2 = datetime.datetime(2021,9,23).date()
plt.axvline(ban1, color='w', lw=1, linestyle='--')
plt.axvline(ban2, color='w', lw=1, linestyle='--')
plt.savefig('article/images/region-stackplot.png', bbox_inches='tight')
plt.close(fig)

# run basic analysis of block labels for output to article
results = Results()
classifier = BlockClassifier()
block_labels = read_csv_date('output/block-labels.csv')
block_labels_sums = block_labels.sum()
total_blocks = block_labels_sums.sum()
unknown_blocks = block_labels_sums['unknown']
known_by_extra_data = sum(block_labels_sums.filter(regex='extraData'))
known_by_miner = sum(block_labels_sums.filter(regex='pool'))

pcts = {
    'known_by_extra_data': known_by_extra_data/total_blocks,
    'known_by_miner': known_by_miner/total_blocks,
    'unknown_blocks': unknown_blocks/total_blocks
}

for k,v in pcts.items():
    results[f'{k}_pct'] = f'{100*v:0.0f}\%'
    
counts = {
    'extra_data_region': len(set([e for r,e in classifier.extra_data_label_regex])),
    'extra_data_regex': len(classifier.extra_data_label_regex),
    'mining_pool': len(block_labels.filter(regex='pool').columns)
}
for k,v in counts.items():
    results[f'{k}_count'] = v
    
results.write()