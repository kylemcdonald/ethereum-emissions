import pandas as pd
import datetime
import numpy as np
from emissions_utils import dot, normalize_row_to_one, read_csv_date

# load mapping from year and grid to an emissions factor
grid_emissions_factors = pd.read_csv('input/grid-emissions-factors.csv').set_index('grid')

# load mapping from a region to distribution across grid, and normalize
region_to_grid_mix = pd.read_csv('input/region-to-grid-mix.csv').set_index('region')
region_to_grid_mix = normalize_row_to_one(region_to_grid_mix.fillna(0))

# load mapping from mining pool to distribution across regions, dropping unknown pools
miner_to_region_mix = pd.read_csv('input/miner-to-region-mix.csv').set_index('miner')
miner_to_region_mix = miner_to_region_mix.drop(columns=['url'])#, 'unknown'])
miner_to_region_mix = miner_to_region_mix.dropna(how='all')
miner_to_region_mix = normalize_row_to_one(miner_to_region_mix.fillna(0))

# construct a mapping from block labels to region mix
miner_label_to_region_mix = miner_to_region_mix.copy()
miner_label_to_region_mix.index = ['pool:' + e for e in miner_label_to_region_mix.index]
region_label_to_region_mix = pd.DataFrame({region:{region:1} for region in region_to_grid_mix.index})
region_label_to_region_mix.index = ['extraData:' + e for e in region_label_to_region_mix.index]
label_to_region_mix = pd.concat((miner_label_to_region_mix, region_label_to_region_mix)).fillna(0)

# manually add an entry for 'unknown' label mapping it to 'unknown' region
label_to_region_mix = label_to_region_mix.append(pd.Series(0, index=label_to_region_mix.columns, name='unknown'))
label_to_region_mix.loc['unknown', 'unknown'] = 1

# linearly interpolate the region_to_grid_mix and grid_emissions_factors from yearly factors to daily factors
daily_emissions_factor = dot(region_to_grid_mix, grid_emissions_factors).T
daily_emissions_factor.index = [datetime.datetime(int(year), 7, 1) for year in daily_emissions_factor.index]
first_year = daily_emissions_factor.index[0].replace(month=1, day=1)
first_year_data = daily_emissions_factor.values[0]
last_year = daily_emissions_factor.index[-1].replace(month=12, day=31)
last_year_data = daily_emissions_factor.values[-1]
daily_emissions_factor.loc[first_year] = first_year_data
daily_emissions_factor.loc[last_year] = last_year_data
daily_emissions_factor = daily_emissions_factor.sort_index().resample('D').interpolate('linear')

# load block labels
block_labels = read_csv_date('output/block-labels.csv').fillna(0)

# construct mapping date to region distribution, including unknown
date_to_regions_with_unknown = dot(block_labels, label_to_region_mix)
date_to_regions_with_unknown.to_csv('output/region-totals.csv', float_format='%.0f')

# drop 'unknown' and normalize before computing weighted average
label_to_region_mix.drop(columns=['unknown'], inplace=True)
block_labels.drop(columns=['unknown'], inplace=True)
block_labels = normalize_row_to_one(block_labels)

# construct mapping from date to region distribution
date_to_regions = dot(block_labels, label_to_region_mix)

# compute the dot product between each daily region distribution, and the emissions factors on that day
emissions_factors = []
for date, row in date_to_regions.fillna(0).iterrows():
    emissions_factors.append(row @ daily_emissions_factor.loc[date])

# fix some glitchy emissions factors from the first 3 weeks
emissions_factors = np.asarray(emissions_factors)
emissions_factors[:20].fill(np.nanmedian(emissions_factors[:20]))

# save the output
df = pd.DataFrame(zip(date_to_regions.index, emissions_factors), columns=['Date', 'Emissions Factor'])
df.set_index('Date').to_csv('output/emissions-factors.csv', float_format='%0.2f')