import copy
import csv
import glob
import logging
import os
from datetime import datetime, timedelta

import pandas as pd

from utils import sha1sum, write_timestamp_file


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__file__)

covid_data_path = os.getenv('COVID_DATA_PATH')
assert covid_data_path, 'COVID_DATA_PATH env variable must be set. (The location of the COVID-DATA folder)'
SOURCE_FILE = max(glob.glob(os.path.join(covid_data_path, 'EPI') + '/dnevni_prikazi*.xlsx'))  # take latest
logger.info(f'SOURCE_FILE: {SOURCE_FILE}')
CSV_FOLDER = os.path.join(os.path.dirname(__file__), '../csv')


def export_dataframe_to_csv(name: str, dataframe):
    filename = os.path.join(CSV_FOLDER, f'{name}.csv')
    old_hash = sha1sum(filename)
    dataframe.replace({0: None}).astype('Int64').to_csv(filename, line_terminator='\r\n')
    write_timestamp_file(filename=filename, old_hash=old_hash)


municipalities = {}
with open(os.path.join(CSV_FOLDER, 'dict-municipality.csv')) as f:
    for row in csv.DictReader(f):
        municipalities[row['name'].lower()] = row
        if row['name_alt']:
            municipalities[row['name_alt'].lower()] = row


def get_municipality_header(municipality: str):
    """ Transforms municipality name from NIJZ xlsx to the municipality header used in final CSVs.
        For instance: Sveti Andraž v Slov.goricah --> region.mb.sveti_andraž_v_slovenskih_goricah
    """
    if municipality == 'NEZNANO':
        return 'region.n.neznano'
    if municipality == 'TUJINA':
        return 'region.t.tujina'
    m = municipality.lower()
    if m == 'sveti andraž v slov.goricah':  # handle typo in xlsx
        m = 'sveti andraž v slov. goricah'
    region = municipalities[m]['region']
    id_ = municipalities[m]['id']
    return f'region.{region}.{id_}'


df = pd.read_excel(io=SOURCE_FILE, sheet_name='Tabela 3', engine='openpyxl', skiprows=[0, 2], skipfooter=1).transpose()[:-1]
df.columns = df.iloc[0]  # sets the header to municipality name instead of having a zero-based index for header
df = df[1:]  # now that municipality is set for the header, we can delete it from the value matrix

df.index.rename('date', inplace=True)  # rename the index since what's contained there are actual dates
df = df.rename(mapper=get_municipality_header, axis='columns')  # transform of municipality names
df = df.rename(mapper=lambda x: datetime.strptime(x, '%d.%m.%Y'), axis='rows')  # transforms strings to datetime
df = df.reindex(sorted(df.columns), axis=1)  # sorts the columns
export_dataframe_to_csv(name='regions', dataframe=df.cumsum())

df = df.rolling(min_periods=1, window=14).sum().replace({0: None}).astype('Int64') \
    .drop('region.n.neznano', axis='columns')
export_dataframe_to_csv(name='active-regions', dataframe=df)

with open(os.path.join(CSV_FOLDER, 'dict-municipality.csv')) as f:
    for row in csv.DictReader(f):
        municipalities[row['name'].lower()] = row
        if row['name_alt']:
            municipalities[row['name_alt'].lower()] = row

# --- deceased-regions.csv ---
# Copy paste latest row for every missing date
deceased_regions_csv_path = os.path.join(CSV_FOLDER, 'deceased-regions.csv')
old_hash = sha1sum(deceased_regions_csv_path)
with open(deceased_regions_csv_path) as f:
    rows = [row for row in csv.DictReader(f)]

latest_date = str([val for val in df.index.values][-1]).split('T')[0]
latest_date = datetime.strptime(latest_date, '%Y-%m-%d').date()
while (date := datetime.strptime(rows[-1]['date'], '%Y-%m-%d').date()) < latest_date:
    rows.append(copy.deepcopy(rows[-1]))
    rows[-1]['date'] = str(date + timedelta(days=1))
# Write the rows collection back to the csv
with open(deceased_regions_csv_path, 'w', newline='') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=rows[0].keys())
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
write_timestamp_file(filename=deceased_regions_csv_path, old_hash=old_hash)

# --- regions-cases.csv | regions-cases-active.csv ---
df = pd.read_excel(io=SOURCE_FILE, sheet_name='Tabela 4', engine='openpyxl', skiprows=[0, 2])[:-1]
df.drop(['SKUPAJ'], inplace=True, axis=1)  # axis=1 means columns


def get_region_header(region: str):
    return {
        'Pomurska': 'region.ms.todate',
        'Podravska': 'region.mb.todate',
        'Koroška': 'region.sg.todate',
        'Savinjska': 'region.ce.todate',
        'Zasavska': 'region.za.todate',
        'Posavska': 'region.kk.todate',
        'Jugovzhodna Slovenija': 'region.nm.todate',
        'Osrednjeslovenska': 'region.lj.todate',
        'Gorenjska': 'region.kr.todate',
        'Primorsko-notranjska': 'region.po.todate',
        'Goriška': 'region.ng.todate',
        'Obalno-kraška': 'region.kp.todate',
        'TUJINA': 'region.foreign.todate',
        'NEZNANO': 'region.unknown.todate'
    }.get(region, 'date')  # if there's no match we assume it's a date column


df = df.rename(mapper=get_region_header, axis='columns')  # transform of region names
df.set_index('date', inplace=True)  # we have zero-based index by default which is obsolete therefore replace with date
df = df.rename(mapper=lambda x: datetime.strptime(x, '%d.%m.%Y'), axis='rows')  # transforms strings to datetime
df = df.reindex(sorted(df.columns), axis=1)  # sorts the columns

df_regions_cases = df.copy(deep=True)
df_regions_cases.loc[:, 'region.todate'] = df_regions_cases.sum(axis=1)  # sums of each row in the column at the end
export_dataframe_to_csv(name='regions-cases', dataframe=df_regions_cases.cumsum())

df_regions_cases_active = df.copy(deep=True)
df_regions_cases_active.loc[:, 'region.active'] = df_regions_cases_active.sum(axis=1)  # sums of each row in the column at the end
df_regions_cases_active = df_regions_cases_active.rename(mapper=lambda x: x.replace('todate', 'active'), axis='columns') \
    .rolling(min_periods=1, window=14).sum().replace({0: None}).astype('Int64') \
    .drop('region.unknown.active', axis='columns')
export_dataframe_to_csv(name='regions-cases-active', dataframe=df_regions_cases_active)

# --- age-confirmed.csv ---
df = pd.read_excel(io=SOURCE_FILE, sheet_name='Tabela 5', engine='openpyxl', skiprows=[1, 2, 3])[:-1]
df.rename(columns={'Dnevno število potrjenih primerov po spolu in starostnih skupinah': 'date'}, inplace=True)
df.set_index('date', inplace=True)
df.rename(mapper=lambda x: datetime.strptime(x, '%d.%m.%Y'), axis='rows', inplace=True)

columns = []
for gender in ['male.', 'female.', 'unknown.', '']:
    for age_range in ['0-4.', '5-14.', '15-24.', '25-34.', '35-44.', '45-54.', '55-64.', '65-74.', '75-84.', '85+.', '']:
        columns.append(f'age.{gender}{age_range}todate')
df.columns = columns

export_dataframe_to_csv(name='age-cases', dataframe=df.cumsum())

# --- cases.csv ---
df_1 = pd.read_excel(io=SOURCE_FILE, sheet_name='Tabela 1', engine='openpyxl', skiprows=[0], skipfooter=1) \
    .drop('Unnamed: 0', axis='columns').rename(mapper={
        'Datum izvida': 'date',
        'SKUPAJ': 'cases.confirmed',
        'Skupaj kumulativno': 'cases.confirmed.todate'
    }, axis='columns').set_index('date') \
    .rename(mapper=lambda x: datetime.strptime(x, '%d.%m.%Y'), axis='rows')[['cases.confirmed', 'cases.confirmed.todate']]
df_1['cases.active'] = df_1['cases.confirmed'].rolling(window=14).sum().astype('Int64')
df_1['cases.closed.todate'] = df_1['cases.confirmed.todate'] - df_1['cases.active']

df_6 = pd.read_excel(io=SOURCE_FILE, sheet_name='Tabela 6', engine='openpyxl', skiprows=[0, 2], skipfooter=2) \
    .rename(mapper={'Datum izvida': 'date', 'Oskrbovanci': 'cases.rh.occupant.confirmed'}, axis='columns').set_index('date') \
    .rename(mapper=lambda x: datetime.strptime(x, '%d.%m.%Y'), axis='rows')[['cases.rh.occupant.confirmed']]
df_6['cases.rh.occupant.confirmed.todate'] = df_6['cases.rh.occupant.confirmed'].cumsum()

df_stats_legacy = pd.read_csv(os.path.join(CSV_FOLDER, 'stats-legacy.csv'), index_col='date')[[
    'cases.hs.employee.confirmed.todate',
    'cases.rh.employee.confirmed.todate'
]]

export_dataframe_to_csv(name='cases', dataframe=df_1.join(df_6).join(df_stats_legacy))