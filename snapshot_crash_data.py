# snapshot_crash_data.py

import os
import pytz
import pandas as pd
from datetime import datetime

import argparse
parser = argparse.ArgumentParser()
parser.add_argument('-f', '--force-refresh', action='store_true', help='Download a copy even if it has already happened today')
args = parser.parse_args()

tz = pytz.timezone('America/Denver')
time_format_string = '%Y_%m_%d__%H_%M'


def current_time():

    now_local = datetime.now(tz)
    
    # Hour of day: '%-I:%M %p'
    # Day of month, year: '%B %-d, %Y')
    return now_local.strftime(time_format_string)



def file_has_been_downloaded_today():

    now_local = datetime.now(tz)
    today = now_local.strftime('%Y_%m_%d')

    snapshots = os.listdir('data/')
    
    todays_snapshots = [f for f in snapshots if today in f]

    return len(todays_snapshots) > 0



def list_all_files():

    return sorted(['data/' + f for f in os.listdir('data/') if '.csv' in f])



def most_recent_file():
    """
    Return the name of the most recent file
    """

    return list_all_files()[-1]


def timestamp_of_most_recent_file():

    return datetime.strptime(most_recent_file(), f'data/denver_crashes_{time_format_string}.csv')
    


def download_file():

    print('Downloading data from denvergov... ', end='')

    df = pd.read_csv(
        'https://www.denvergov.org/media/gis/DataCatalog/traffic_accidents/csv/traffic_accidents.csv'
        , low_memory=False
        )

    print('complete.')

    snapshot_filename = f'data/denver_crashes_{current_time()}.csv'
    df.to_csv(snapshot_filename, index=False)

    print(f'Snapshot saved to: {snapshot_filename}')

    number_of_crashes = len(df)
    print(f'Crashes in dataset: {number_of_crashes:,}')



if __name__ == '__main__':


    # print(datetime.now(tz) - timestamp_of_most_recent_file())

    current_timestamp = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S %Z')
    print(f'{current_timestamp} -> ', end='')

    if (not file_has_been_downloaded_today()) or (args.force_refresh):
        download_file()
    else:
        print('The crash dataset has already been downloaded today.')
