import numpy as np
import datetime
import pandas as pd
from collections import defaultdict
from results import Results
from emissions_utils import read_csv_date,\
    efficiency_at_date,\
    convert_gw_and_ef_to_daily_ktco2,\
    convert_gigawatts_to_twh_per_year,\
    convert_twh_per_year_to_gigawatts,\
    convert_daily_gigawatts_to_twh,\
    convert_mtco2_per_year_to_daily_ktco2,\
    mkdate,\
    date_in_range
import matplotlib.pyplot as plt
plt.rcParams['font.size'] = 20

def plot_annual(results, ylabel, label=None):
    fig = plt.figure(figsize=(20,6), facecolor='white')
    for year in range(2016, 2022):
        plt.axvline(datetime.datetime(year,1,1), color='k', lw=1, linestyle='--')
    plt.plot(dates, results['best'], lw=2, label=label)
    plt.fill_between(dates, results['lower'], results['upper'], alpha=0.25)
    plt.ylabel(ylabel)    
    plt.ylim(0)    
    plt.xlim(min(dates), max(dates))
    return fig

# load data from previous run
df = read_csv_date('output/emissions-factors.csv')
factors = {k.date():v for k,(v,) in df.iterrows()}
df = read_csv_date('output/daily-gw.csv')
power_results = dict(zip(df.columns, df.T.values))
df = read_csv_date('output/daily-ktco2.csv')
emissions_results = dict(zip(df.columns, df.T.values))
dates = [e.date() for e in df.index]

# plot energy
fig = plot_annual(power_results, 'Gigawatts', 'This study')

digi_energy = pd.read_csv('other-studies/digiconomist-energy.csv')
digi_dates = [e.date() for e in pd.to_datetime(digi_energy['Date'])]
digi_estimate = convert_twh_per_year_to_gigawatts(digi_energy['Estimated TWh per Year'].values)
digi_minimum = convert_twh_per_year_to_gigawatts(digi_energy['Minimum TWh per Year'].values)
plt.plot(digi_dates, digi_estimate, lw=2, label='De Vries estimate', linestyle='dotted')
plt.plot(digi_dates, digi_minimum, lw=2, label='De Vries minimum', linestyle='dotted')

krause = pd.read_csv('other-studies/krause-tolaymat.csv')
krause_dates = [e.date() for e in pd.to_datetime(krause['Date'])]
krause_estimate_mw = krause['MW'].values
krause_estimate_gw = krause_estimate_mw / 1e3
plt.plot(krause_dates, krause_estimate_gw, label='Krause', lw=2, linestyle=(0,(8,4)))

gallersdoerfer_2020_3_27_twh = 6.299
gallersdoerfer_2020_3_27_gw = convert_twh_per_year_to_gigawatts(gallersdoerfer_2020_3_27_twh)
gallersdoerfer_dates = [datetime.datetime(2020, 3, 27).date()]
gallersdoerfer_estimate = [gallersdoerfer_2020_3_27_gw]
plt.scatter(gallersdoerfer_dates, gallersdoerfer_estimate, label='Gallersdörfer', lw=2, marker='*', color='yellow', edgecolors='k', s=500, clip_on=False)

ax = plt.gca().secondary_yaxis('right')
twh_labels = np.linspace(0,50,11).astype(int)
twh_in_gw = convert_twh_per_year_to_gigawatts(twh_labels)
ax.set_yticks(twh_in_gw, labels=twh_labels)
ax.set_ylabel('Terawatt hours/year')

plt.legend()
plt.savefig('article/images/power.png', bbox_inches='tight')
plt.close(fig)

# plot emissions
fig = plot_annual(emissions_results, 'ktCO$_2$/day', 'This study')

plt.plot(digi_dates, convert_gw_and_ef_to_daily_ktco2(digi_estimate, 475), lw=2, label='De Vries estimate', linestyle='dotted')
plt.plot(digi_dates, convert_gw_and_ef_to_daily_ktco2(digi_minimum, 475), lw=2, label='De Vries minimum', linestyle='dotted')

plt.plot(krause_dates, convert_gw_and_ef_to_daily_ktco2(krause_estimate_gw, 193), lw=2, label='Krause lower', linestyle=(0,(8,4)))
plt.plot(krause_dates, convert_gw_and_ef_to_daily_ktco2(krause_estimate_gw, 914), lw=2, label='Krause upper', linestyle=(0,(8,4)))

ax = plt.gca().secondary_yaxis('right')
mtco2_labels = np.linspace(0,20,11).astype(int)
mtco2_in_ktco2 = convert_mtco2_per_year_to_daily_ktco2(mtco2_labels)
ax.set_yticks(mtco2_in_ktco2, labels=mtco2_labels)
ax.set_ylabel('Megatons CO$_2$/year')

plt.ylim(0,35)
plt.legend()
plt.savefig('article/images/emissions.png', bbox_inches='tight')
plt.close(fig)

# plot emissions factors
fig = plt.figure(figsize=(20,6), facecolor='white')
for year in range(2016, 2022):
    plt.axvline(datetime.datetime(year,1,1), color='k', lw=1, linestyle='--')
plt.plot(dates, [factors[e] for e in dates])
plt.xlim(dates[0], dates[-1])
plt.ylim(200, 400)
plt.ylabel('gCO$_2$/kWh')
plt.savefig('article/images/emissions-factors.png', bbox_inches='tight')
plt.close(fig)

results = Results()

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

eff_at_start = efficiency_at_date(dates[0])
eff_at_end = efficiency_at_date(dates[-1])
results['eff_at_start'] = f'\eff{{{eff_at_start:0.2f}}}'
results['eff_at_end'] = f'\eff{{{eff_at_end:0.2f}}}'
results['eff_end_date'] = f'{dates[-1]}'

results.write()