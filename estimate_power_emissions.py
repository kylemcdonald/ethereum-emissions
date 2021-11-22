import numpy as np
import datetime
import pandas as pd
import json
from collections import defaultdict
from emissions_utils import read_csv_date, convert_gw_and_ef_to_daily_ktco2, efficiency_at_date

with open('input/power-parameters.json') as f:
    params = json.load(f)

emissions_factors = read_csv_date('output/emissions-factors.csv')
emissions_factors = {k.date():v for k,(v,) in emissions_factors.iterrows()}

hashrate_history_ghps = read_csv_date('input/hashrate.csv', index='Date(UTC)')
dates = [e.date() for e in hashrate_history_ghps.index]
hashrate_history_ghps = hashrate_history_ghps['Value'].values

def compute_instant_power(
    hashrate, # ethereum network hashrate (megahashes per second)
    hashing_efficiency, # average hasing efficiency (megahashes per second per watt)
    hashing_efficiency_offset, # offset from mean hashing efficiency (megahashes per second per watt)
    datacenter_overhead,
    hardware_overhead,
    grid_loss,
    psu_efficiency):
    hashing_efficiency += hashing_efficiency_offset
    instant = (hashrate * datacenter_overhead * hardware_overhead * grid_loss) / \
        (hashing_efficiency * psu_efficiency)
    return instant

daily_gw = defaultdict(list)
daily_ktco2 = defaultdict(list)
for date, hashrate_ghps in zip(dates, hashrate_history_ghps):
    hashrate_mhps = hashrate_ghps * 1e3
    hashing_efficiency = efficiency_at_date(date)
    
    for k,v in params.items():
        instant_power_watts = compute_instant_power(hashrate_mhps, hashing_efficiency, **v)
        instant_power_gigawatts = instant_power_watts / 1e9
        daily_gw[k].append(instant_power_gigawatts)
        
        daily_emissions_kilotons = convert_gw_and_ef_to_daily_ktco2(instant_power_gigawatts, emissions_factors[date])
        daily_ktco2[k].append(daily_emissions_kilotons)

pd.DataFrame(daily_gw, index=pd.Series(dates, name='Date')).to_csv('output/daily-gw.csv', float_format='%0.6f')
pd.DataFrame(daily_ktco2, index=pd.Series(dates, name='Date')).to_csv('output/daily-ktco2.csv', float_format='%0.6f')