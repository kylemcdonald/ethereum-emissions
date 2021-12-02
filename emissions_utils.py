import pandas as pd
import datetime
from itertools import islice, chain

def chunks(x, n):
    # return slices of lists
    if hasattr(x, '__len__'):
        for i in range(0, len(x), n):
            yield x[i:i+n]
    else:
        # return sub-generators of generators
        i = iter(x)
        for e in i:
            yield chain([e], islice(i, n-1))
            
def normalize_row_to_one(df):
    return df.div(df.sum(axis=1), axis=0)

def dot(a, b):
    return a @ b.T[a.columns].T

def read_csv_date(fn, index='Date'):
    df = pd.read_csv(fn).set_index(index)
    df.index = pd.to_datetime(df.index)
    return df

def efficiency_at_date(date):
    z = (1.3744496623898123e-09, -1.81046377784513) # from GPU Efficiency notebook
    dt = datetime.datetime(date.year, date.month, date.day)
    timestamp = datetime.datetime.timestamp(dt)
    return timestamp * z[0] + z[1]

def combine_and_rename(data, groups):
    to_drop = []
    rename_map = {}
    for k,v in groups.items():
        base = v[0]
        rename_map[base] = k
        for e in v[1:]:
            data[base] += data[e]
            to_drop.append(e)
    data.drop(columns=to_drop, inplace=True)
    data.rename(rename_map, axis=1, inplace=True)
    return data

def convert_gw_and_ef_to_daily_ktco2(daily_gw, ef):
    daily_kwh = daily_gw * 24 * 1e6
    daily_gco2 = daily_kwh * ef
    daily_ktco2 = daily_gco2 / 1e9
    return daily_ktco2

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

# convert a list of daily average gw power to total terawatt hours
def convert_daily_gigawatts_to_twh(daily_gigawatts):
    gigawatt_hours = sum(daily_gigawatts) * 24
    terawatt_hours = gigawatt_hours / 1e3
    return terawatt_hours

def convert_mtco2_per_year_to_daily_ktco2(mtco2):
    return (mtco2 / 365) * 1e3

def mkdate(y,m,d):
    return datetime.datetime(y,m,d).date()

def date_in_range(x, begin, end):
    return begin <= x and x <= end