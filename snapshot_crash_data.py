# snapshot_crash_data.py

import os
import pytz
import argparse
import requests
import pandas as pd
import sqlite3 as sq
from pathlib import Path
from datetime import datetime



class SnapshotCrashData():

    def __init__(self):

        parser = argparse.ArgumentParser()
        parser.add_argument('-f', '--force-refresh', action='store_true', help='Download a copy even if it has already happened today')
        self.args = parser.parse_args()

        self.header_file = Path('data/remote_header_etag.txt')
        if not self.header_file.exists():
            with open(self.header_file, 'w') as f:
                f.write('remote_header_has_not_yet_been_downloaded')

        self.url = 'https://www.denvergov.org/media/gis/DataCatalog/traffic_accidents/csv/traffic_accidents.csv'

        self.tz = pytz.timezone('America/Denver')

        # Hour of day: '%-I:%M %p'
        # Day of month, year: '%B %-d, %Y')
        self.time_format_string = '%Y_%m_%d__%H_%M'



    def current_time(self):

        now_local = datetime.now(self.tz)
        
        return now_local.strftime(self.time_format_string)



    def remote_file_has_new_header(self):
        """
        Return True if the remote header has a ETag value that is different from the local version
        """

        with open(self.header_file, 'r') as f:
            old_header_etag = f.read()

        r = requests.head(self.url)
        self.remote_header_etag = r.headers['ETag']

        return self.remote_header_etag != old_header_etag
        


    def write_new_etag_to_file(self):
        """Write the ETag from the remote header file to the local text file"""

        with open(self.header_file, 'w') as f:
            f.write(self.remote_header_etag)



    def download_file(self):

        print('Downloading data from denvergov... ', end='')

        conn = sq.connect('data/denver_crashes.sqlite')

        df = pd.read_csv(self.url, low_memory=False)

        print('complete.')

        df.to_sql('crashes', conn, if_exists='replace')
        conn.close()
        print(f'Snapshot saved to: denver_crashes.sqlite')
        
        # snapshot_filename = f'data/denver_crashes_{self.current_time()}.csv'
        # df.to_csv(snapshot_filename, index=False)

        # print(f'Snapshot saved to: {snapshot_filename}')

        number_of_crashes = len(df)
        print(f'Crashes in dataset: {number_of_crashes:,}')

        self.write_new_etag_to_file()



    def run(self):

        current_timestamp = datetime.now(self.tz).strftime('%Y-%m-%d %H:%M:%S %Z')
        print(f'{current_timestamp} -> ', end='')

        if (self.remote_file_has_new_header()) or (self.args.force_refresh):
            self.download_file()
        else:
            print('Local data matches remote data.')



if __name__ == '__main__':

    scd = SnapshotCrashData()
    scd.run()

