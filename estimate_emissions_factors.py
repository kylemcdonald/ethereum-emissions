from tqdm import tqdm
from results import Results
results = Results()

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

from block_index import BlockIndex
from block_classifier import BlockClassifier

import datetime
import json
from collections import defaultdict, Counter
from itertools import islice

plt.rcParams['font.size'] = 20

index = BlockIndex(read_only=True)
classifier = BlockClassifier()

# this whole section should be pre-computed
# instead of sitting in this script
# so it can be checked for errors
def normalize_row_to_one(df):
    return df.div(df.sum(axis=1), axis=0)

emissions_factors = pd.read_csv('data/emissions-factors.csv').set_index('Region')
label_mix = pd.read_csv('data/label-mix.csv').set_index('label')
label_mix = normalize_row_to_one(label_mix.fillna(0))
label_to_emissions_factor = label_mix @ emissions_factors
label_to_emissions_factor.columns = label_to_emissions_factor.columns.map(int)
lookup_emissions_factor_by_label = label_to_emissions_factor.T.to_dict()

mining_regions = pd.read_csv('data/mining-regions.csv').set_index('miner')
lookup_emissions_factor_by_miner = {}
region_names = ['europe','us','asia','china','russia']
for miner in mining_regions.index:
    factors = []
    for region_name in region_names:
        weight = mining_regions.loc[miner,region_name]
        factor = label_to_emissions_factor.loc[region_name]
        if weight != weight:
            continue
        factors.append((weight, factor))
    if len(factors) == 0:
        continue
    factors = sum([w*f for w,f in factors]) / sum([w for w,f in factors])
    lookup_emissions_factor_by_miner[miner] = factors.to_dict()

# this is where we classify extraData or mining pool into an emissions factor
extra_data_samples = []
miner_samples = []
emissions_factor_samples = []
known_by_extra_data = 0
known_by_miner = 0

total = index.latest_block() - 1
for block in tqdm(index.list_blocks(skip_genesis=True), total=total):
    date = block.get_datetime().date()
    
    sample = None
    
    label = classifier.classify_extra_data(block.extra_data)
    if label is None:
        label = 'unknown'
    elif label in lookup_emissions_factor_by_label:
        factor = lookup_emissions_factor_by_label[label][date.year]
        sample = (date, factor)
        known_by_extra_data += 1
    extra_data_samples.append((date, label))
    
    label = classifier.classify_miner(block.miner)
    if label is None:
        label = 'unknown'
    elif sample is None and label in lookup_emissions_factor_by_miner:
        factor = lookup_emissions_factor_by_miner[label][date.year]
        sample = (date, factor)
        known_by_miner += 1
    miner_samples.append((date, label))
    
    if sample is not None:
        emissions_factor_samples.append(sample)

def list_dates(start_date, end_date):
    dates = []
    date = start_date
    while date <= end_date:
        dates.append(date)
        date += datetime.timedelta(days=1)
    return dates

def average_by_day(samples):
    samples.sort()
    
    begin_date = samples[0][0]
    end_date = samples[-1][0]
    dates = list_dates(begin_date, end_date)
    
    grouped = defaultdict(list)
    for date, e in samples:
        grouped[date].append(e)
        
    averages = [np.mean(grouped[e]) if len(grouped[e]) else 0 for e in dates]
    return dates, averages

dates, averages = average_by_day(emissions_factor_samples)

# fix first 20 days
averages = np.asarray(averages)
averages[:20].fill(np.median(averages[:20]))

# export for other scripts to use
# need to change this a different folder
pd.DataFrame(zip(dates, averages), columns=['Date', 'Emissions Factor']).set_index('Date').to_csv('data/factors.csv')

# we only need the rest for the article
known_blocks = len(emissions_factor_samples)
total_blocks = index.latest_block()

pcts = {
    'known_by_extra_data': known_by_extra_data/total_blocks,
    'known_by_miner': known_by_miner/total_blocks,
    'unknown_blocks': 1-(known_blocks/total_blocks)
}
for k,v in pcts.items():
    results[f'{k}_pct'] = f'{100*v:0.0f}\%'
    
regex_regions = set([e for r,e in classifier.extra_data_label_regex])

counts = {
    'extra_data_region': len(set(regex_regions)),
    'extra_data_regex': len(classifier.extra_data_label_regex),
    'mining_pool': len(lookup_emissions_factor_by_miner)
}
for k,v in counts.items():
    results[f'{k}_count'] = v

def daily_distribution(samples, normalize=True):
    samples.sort()
    
    begin_date = samples[0][0]
    end_date = samples[-1][0]
    dates = list_dates(begin_date, end_date)

    unique_labels = list(sorted(set([e[1] for e in samples])))
    label_to_index = {e:i for i,e in enumerate(unique_labels)}
    by_label = np.zeros((len(unique_labels), len(dates)), int)

    for date, label in samples:
        index = label_to_index[label]
        offset = (date - begin_date).days
        by_label[index, offset] += 1

    normalized = by_label.astype(float)
    if normalize:
        normalized /= normalized.sum(0)
    normalized[np.isnan(normalized)] = 0
    
    return dates, unique_labels, normalized

def draw_ratios(dates, labels, data, legend=False, legend_n=8):
    indices = np.argsort(data.sum(1))[::-1]
    fig = plt.figure(figsize=(20,5), facecolor='white')
    plt.stackplot(dates, data[indices], lw=0, labels=[labels[i] for i in indices])
    plt.xlim(dates[0], dates[-1])
    
    if data.max() == 1:
        plt.ylim(0,1)
    
    if legend:
        n = len(labels)
        plt.legend(ncol=min(n,legend_n),
                   loc='upper center',
                   bbox_to_anchor=(0.5, -0.1))

    return fig
    
def draw_samples(samples, normalize=True, legend=True, **kwargs):
    return draw_ratios(*daily_distribution(samples, normalize=normalize), legend=legend, **kwargs)

to_collapse = set([
    'ukraine',
    'us-west',
    'russia',
    'taiwan',
    'us-east',
    'singapore'])
collapsed = []
for d,e in extra_data_samples:
    if e in to_collapse:
        collapsed.append((d, 'other'))
    else:
        collapsed.append((d, e))

fig = draw_samples(collapsed, normalize=True, legend_n=5)
ban1 = datetime.datetime(2021,5,21).date()
ban2 = datetime.datetime(2021,9,23).date()
plt.axvline(ban1, color='w', lw=1, linestyle='--')
plt.axvline(ban2, color='w', lw=1, linestyle='--')
plt.yticks([])
plt.savefig('overleaf/images/extra-data-stackplot.png', bbox_inches='tight')
plt.close(fig)

results.write()