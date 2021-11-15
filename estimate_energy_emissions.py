import numpy as np
import datetime
import pandas as pd
import matplotlib.pyplot as plt
from collections import defaultdict
from save_plot import SavePlot

plt.rcParams['font.size'] = 20

# from GPU Efficiency notebook
z = (1.3724361063410362e-09, -1.8072657791038405)
mae = 0.07921742610595504

def to_date(date_str):
    return pd.to_datetime(date_str).date()
    
def date_to_timestamp(e):
    return datetime.datetime.timestamp(datetime.datetime(e.year, e.month, e.day))

def timestamp_to_date(e):
    return datetime.datetime.fromtimestamp(e).date()

def efficiency_at_date(date):
    return efficiency_at_timestamp(date_to_timestamp(date))

def efficiency_at_timestamp(timestamp):
    return timestamp * z[0] + z[1]

dates, factors = zip(*pd.read_csv('data/factors.csv').values)
dates = [pd.to_datetime(e).date() for e in dates]
factors = dict(zip(dates, factors))

hashrate_history = pd.read_csv('data/hashrate.csv')[['Date(UTC)', 'Value']].values

# compute the power from the perspective of the utility provider
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

params = {
    'lower': { # best case scenario
        'hashing_efficiency_offset': 0.08,
        'datacenter_overhead': 1.01,
        'hardware_overhead': 1.03,
        'grid_loss': 1.05,
        'psu_efficiency': 0.95
    },
    'best': { # best guess
        'hashing_efficiency_offset': 0,
        'datacenter_overhead': 1.10,
        'hardware_overhead': 1.03,
        'grid_loss': 1.06,
        'psu_efficiency': 0.90
    },
    'upper': { # worst case scenario
        'hashing_efficiency_offset': -0.08,
        'datacenter_overhead': 1.1,
        'hardware_overhead': 1.08,
        'grid_loss': 1.07,
        'psu_efficiency': 0.80
    }
}

def gw_ef_to_daily_ktco2(daily_gw, ef):
    daily_kwh = daily_gw * 24 * 1e6
    daily_gco2 = daily_kwh * ef
    daily_ktco2 = daily_gco2 / 1e9
    return daily_ktco2

dates = []
power_results = defaultdict(list)
emissions_results = defaultdict(list)
for date, hashrate_gh in hashrate_history:
    hashrate_mh = hashrate_gh * 1000
    date = to_date(date)
    hashing_efficiency = efficiency_at_date(date)
    
    for k,v in params.items():
        instant_power_watts = compute_instant_power(hashrate_mh, hashing_efficiency, **v)
        instant_power_gigawatts = instant_power_watts / 1e9
        power_results[k].append(instant_power_gigawatts)
        
        daily_emissions_kilotons = gw_ef_to_daily_ktco2(instant_power_gigawatts, factors[date])
        emissions_results[k].append(daily_emissions_kilotons)
    
    dates.append(date)

# save for future use
pd.DataFrame((dates, power_results['best'])).T.to_csv('power.csv', index=False, header=['Date', 'Gigawatts'])
pd.DataFrame((dates, emissions_results['best'])).T.to_csv('emissions.csv', index=False, header=['Date', 'ktCO2e/day'])

def convert_gigawatts_to_twh_per_year(gigawatts):
    gigawatt_hours_per_day = gigawatts * 24
    gigawatt_hours_per_year = gigawatt_hours_per_day * 365
    terawatt_hours_per_year = gigawatt_hours_per_year / 1e3
    return terawatt_hours_per_year

def convert_twh_per_year_to_gigawatts(terawatt_hours_per_year):
    gigawatt_hours_per_year = terawatt_hours_per_year * 1e3
    gigawatt_hours_per_day = gigawatt_hours_per_year / 365
    gigawatts = gigawatt_hours_per_day / 24
    return gigawatts

def convert_daily_gigawatts_to_twh(daily_gigawatts):
    gigawatt_hours = sum(daily_gigawatts) * 24
    terawatt_hours = gigawatt_hours / 1e3
    return terawatt_hours

# this is the part we do for the article, should be separated out
import datetime

def plot_annual(results, ylabel, label=None):
    fig = plt.figure(figsize=(20,6), facecolor='white')
    for year in range(2016, 2022):
        plt.axvline(datetime.datetime(year,1,1), color='k', lw=1, linestyle='--')
    plt.plot(dates, results['best'], lw=2, label=label)
    
    lw = 1
    alpha = 0.25
    color = 'gray'
    plt.fill_between(dates, results['lower'], results['upper'], alpha=alpha)
    plt.ylabel(ylabel)    
    plt.ylim(0)    
    plt.xlim(min(dates), max(dates))
    
    return fig
    
saver = SavePlot()

# plot energy
fig = plot_annual(power_results, 'Gigawatts', 'This study')

for e in ['best','lower','upper']:
    saver.add(dates, power_results[e], f'McDonald GW {e}')

digi_energy = pd.read_csv('data/digiconomist-energy.csv')
digi_dates = [e.date() for e in pd.to_datetime(digi_energy['Date'])]
digi_estimate = convert_twh_per_year_to_gigawatts(digi_energy['Estimated TWh per Year'].values)
digi_minimum = convert_twh_per_year_to_gigawatts(digi_energy['Minimum TWh per Year'].values)
plt.plot(digi_dates, digi_estimate, lw=2, label='De Vries estimate', linestyle='dotted')
plt.plot(digi_dates, digi_minimum, lw=2, label='De Vries minimum', linestyle='dotted')

saver.add(digi_dates, digi_estimate, 'De Vries GW estimate')
saver.add(digi_dates, digi_minimum, 'De Vries GW minimum')

krause = pd.read_csv('data/Krause Tolaymat - Sheet1.csv')
krause_dates = [e.date() for e in pd.to_datetime(krause['Date'])]
krause_estimate_mw = krause['MW'].values
krause_estimate_gw = krause_estimate_mw / 1e3
plt.plot(krause_dates, krause_estimate_gw, label='Krause', lw=2, linestyle=(0,(8,4)))

saver.add(krause_dates, krause_estimate_gw, 'Krause GW')

gallersdoerfer_2020_3_27_twh = 6.299
gallersdoerfer_2020_3_27_gw = convert_twh_per_year_to_gigawatts(gallersdoerfer_2020_3_27_twh)
gallersdoerfer_dates = [datetime.datetime(2020, 3, 27).date()]
gallersdoerfer_estimate = [gallersdoerfer_2020_3_27_gw]
plt.scatter(gallersdoerfer_dates, gallersdoerfer_estimate, label='Gallersdörfer', lw=2, marker='*', color='k', s=200)

saver.add(gallersdoerfer_dates, gallersdoerfer_estimate, 'Gallersdörfer GW')

plt.legend()
plt.savefig('overleaf/images/power.png', bbox_inches='tight')
plt.close(fig)

# plot emissions
fig = plot_annual(emissions_results, 'ktCO$_2$/day', 'This study')

for e in ['best','lower','upper']:
    saver.add(dates, power_results[e], f'McDonald ktCO2/day {e}')

def mkdate(y,m,d):
    return datetime.datetime(y,m,d).date()

plt.plot(digi_dates, gw_ef_to_daily_ktco2(digi_estimate, 475), lw=2, label='De Vries estimate', linestyle='dotted')
plt.plot(digi_dates, gw_ef_to_daily_ktco2(digi_minimum, 475), lw=2, label='De Vries minimum', linestyle='dotted')

saver.add(digi_dates, gw_ef_to_daily_ktco2(digi_estimate, 475), 'De Vries ktCO2/day estimate')
saver.add(digi_dates, gw_ef_to_daily_ktco2(digi_minimum, 475), 'De Vries ktCO2/day minimum')

plt.plot(krause_dates, gw_ef_to_daily_ktco2(krause_estimate_gw, 193), lw=2, label='Krause lower', linestyle=(0,(8,4)))
plt.plot(krause_dates, gw_ef_to_daily_ktco2(krause_estimate_gw, 914), lw=2, label='Krause upper', linestyle=(0,(8,4)))

saver.add(krause_dates, gw_ef_to_daily_ktco2(krause_estimate_gw, 193), 'Krause ktCO2/day lower')
saver.add(krause_dates, gw_ef_to_daily_ktco2(krause_estimate_gw, 914), 'Krause ktCO2/day upper')

plt.legend()
plt.savefig('overleaf/images/emissions.png', bbox_inches='tight')
plt.close(fig)

# plot emissions factors
plt.figure(figsize=(20,6), facecolor='white')
for year in range(2016, 2022):
    plt.axvline(datetime.datetime(year,1,1), color='k', lw=1, linestyle='--')
plt.plot(dates, [factors[e] for e in dates])
plt.xlim(dates[0], dates[-1])
plt.ylim(350, 550)
plt.ylabel('gCO$_2$/kWh')
plt.savefig('overleaf/images/emissions-factors.png', bbox_inches='tight')
plt.show()


saver.add(dates, [factors[e] for e in dates], 'gCO2/kWh')

# update all results
from results import Results
results = Results()

def date_in_range(x, begin, end):
    return begin <= x and x <= end

def emissions_kt_on_date(date):
    for d,e in zip(dates, emissions_results['best']):
        if d == date:
            return e

def cumulative_emissions_kt_to_date(date):
    total_kt = 0
    for d,e in zip(dates, emissions_results['best']):
        total_kt += e
        if d == date:
            break
    return total_kt

peak = np.argmax(power_results['best'])
peak_date = dates[peak].isoformat()
results['peak_date'] = peak_date

for e in ['best','lower','upper']:
    energy = convert_gigawatts_to_twh_per_year(power_results[e][peak])
    results[f'peak_energy_{e}'] = f'\SI{{{energy:.0f}}}{{\TWh}}'
    
for e in ['best','lower','upper']:
    power = power_results[e][peak]
    results[f'peak_power_{e}'] = f'\SI{{{power:.1f}}}{{\giga\watt}}'

total_energy_2018 = np.mean([e for d,e in zip(dates, power_results['best']) if d.year == 2018])
total_energy_2018 = convert_gigawatts_to_twh_per_year(total_energy_2018)
results['total_energy_2018'] = f'\SI{{{total_energy_2018:0.1f}}}{{\TWh}}'

target = datetime.datetime(2020, 3, 27).date()
total_energy_2020_03_27, = [e for d,e in zip(dates, power_results['best']) if d == target]
total_energy_2020_03_27 = convert_gigawatts_to_twh_per_year(total_energy_2020_03_27)
results['total_energy_2020_03_27'] = f'\SI{{{total_energy_2020_03_27:0.1f}}}{{\TWh}}'

for e in ['best','upper','lower']:
    energy = convert_daily_gigawatts_to_twh(power_results[e])
    results[f'total_energy_{e}'] = f'\SI{{{energy:0.0f}}}{{\TWh}}'
    
for e in ['best','upper','lower']:
    emissions_kt = sum(emissions_results[e])
    emissions_mt = emissions_kt / 1e3
    results[f'total_emissions_{e}'] = f'\mtcotwo{{{emissions_mt:.0f}}}'

peak_emissions = np.argmax(emissions_results['best'])
peak_emissions_date = dates[peak_emissions].isoformat()
results['peak_emissions_date'] = peak_emissions_date

for e in ['best','lower','upper']:
    emissions_kt = emissions_results[e][peak_emissions]
    emissions_kt_annual = emissions_kt * 365
    emissions_mt_annual = emissions_kt_annual / 1e3
    results[f'peak_emissions_annual_{e}'] = f'\mtcotwo{{{emissions_mt_annual:.0f}}}'
    
first_efficiency = efficiency_at_date(dates[0])
results['first_efficiency'] = f'\eff{{{first_efficiency:.2f}}}'

last_efficiency = efficiency_at_date(dates[-1])
results['last_efficiency'] = f'\eff{{{last_efficiency:.2f}}}'

krause_first_date = krause_dates[0]
krause_first_efficiency = 1 / krause['J/MH'].values[0]
results['krause_first_date'] = f'{krause_first_date}'
results['krause_first_efficiency'] = f'\eff{{{krause_first_efficiency:.2f}}}'

krause_last_date = krause_dates[-1]
krause_last_efficiency = 1 / krause['J/MH'].values[-1]
results['krause_last_date'] = f'{krause_last_date}'
results['krause_last_efficiency'] = f'\eff{{{krause_last_efficiency:.2f}}}'

krause_first_efficiency_ours = efficiency_at_date(krause_first_date)
results['krause_first_efficiency_ours'] = f'\eff{{{krause_first_efficiency_ours:.2f}}}'

krause_last_efficiency_ours = efficiency_at_date(krause_last_date)
results['krause_last_efficiency_ours'] = f'\eff{{{krause_last_efficiency_ours:.2f}}}'

krause_begin_emissions_date = datetime.datetime(2016,1,1).date()
krause_end_emissions_date = datetime.datetime(2018,6,30).date()

for k,v in emissions_results.items():
    emissions_kt = [e for e,d in zip(v,dates) if date_in_range(d, krause_begin_emissions_date, krause_end_emissions_date)]
    emissions_kt = sum(emissions_kt)
    emissions_mt = emissions_kt / 1e3
    results[f'krause_emissions_period_{k}'] = f'\mtcotwo{{{emissions_mt:.1f}}}'
    
emissions_min = min(factors.values())
results['emissions_min'] = f'\mtcotwo{{{emissions_min:.0f}}}'

emissions_max = max(factors.values())
results['emissions_max'] = f'\mtcotwo{{{emissions_max:.0f}}}'

de_vries_equivalent_march_kt_day = emissions_kt_on_date(datetime.datetime(2021,3,8).date())
de_vries_equivalent_march_mt_year = de_vries_equivalent_march_kt_day * 365 / 1e3
results['de_vries_equivalent_march'] = f'\ktcotwo{{{de_vries_equivalent_march_mt_year:.1f}}}'

de_vries_equivalent_october_kt_day = emissions_kt_on_date(datetime.datetime(2021,10,8).date())
de_vries_equivalent_october_mt_year = de_vries_equivalent_october_kt_day * 365 / 1e3
results['de_vries_equivalent_october'] = f'\ktcotwo{{{de_vries_equivalent_october_mt_year:.1f}}}'

marro_dates = [mkdate(2021,4,29), mkdate(2021,5,5)]
marro_equivalent = cumulative_emissions_kt_to_date(marro_dates[1]) - cumulative_emissions_kt_to_date(marro_dates[0])
marro_equivalent /= (marro_dates[1] - marro_dates[0]).days
results['marro_equivalent'] = f'\ktcotwo{{{marro_equivalent:.1f}}}'

eff_at_start = efficiency_at_timestamp(datetime.datetime.combine(dates[0], datetime.time()).timestamp())
eff_at_end = efficiency_at_timestamp(datetime.datetime.combine(dates[-1], datetime.time()).timestamp())
results['eff_at_start'] = f'\eff{{{eff_at_start:0.2f}}}'
results['eff_at_end'] = f'\eff{{{eff_at_end:0.2f}}}'
results['eff_end_date'] = f'{dates[-1]}'

results.write()

saver.write('saved-data.csv')