# snapshot_crash_data.py

import os
import pytz
import time
import argparse
import requests
import subprocess
import pandas as pd
from pathlib import Path
from datetime import datetime

from crash_data_analysis import CrashDataAnalysis



class SnapshotCrashData():

    def __init__(self):

        parser = argparse.ArgumentParser()
        parser.add_argument('-f', '--force-refresh', action='store_true', help='Download a copy even if it has already happened today')
        parser.add_argument('-p', '--postgres', action='store_true', help='Preprocess the local raw file and upload to postgres')
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

        self.cda = CrashDataAnalysis()



    def current_time(self):

        now_local = datetime.now(self.tz)
        
        return now_local.strftime(self.time_format_string)



    def remote_file_has_new_header(self):
        """
        Return True if the remote header has a ETag value that is different from the local version
        """

        with open(self.header_file, 'r') as f:
            old_header_etag = f.read()

        try:
            r = requests.head(self.url)
        except Exception as e:
            print('Something went wrong accessing the remote file, so we will not try to download it.')
            return False
        
        self.remote_header_etag = r.headers['ETag']

        if self.remote_header_etag == old_header_etag:
            print('Local data matches remote data.')

        return self.remote_header_etag != old_header_etag
        


    def write_new_etag_to_file(self):
        """Write the ETag from the remote header file to the local text file"""

        with open(self.header_file, 'w') as f:
            f.write(self.remote_header_etag)



    def download_file(self):

        print('Downloading data from denvergov... ', end='')

        try:
            df = pd.read_csv(self.url, low_memory=False)
        except Exception as e:
            print('Something went wrong trying to download the CSV. Quitting.')
            return

        print('complete.')

        df['updated_at'] = datetime.now(pytz.timezone('UTC')).strftime('%Y-%m-%d %H:%M %Z')

        df.to_csv('data/raw_crash_data.csv', index=False)
        print('Raw data saved to: data/raw_crash_data.csv')

        df_preprocessed = self.cda.preprocess_crash_data(df=df, verbose=False, all_columns=False)

        df_preprocessed.to_csv('data/preprocessed_crash_data.csv', index=False)

        number_of_crashes = len(df)
        print(f'Crashes in dataset: {number_of_crashes:,}')

        self.write_new_etag_to_file()



    def push_to_postgres(self):
        """
        Push the most recent local data to Postgres
        """

        start = time.perf_counter()

        with subprocess.Popen(
            f'psql -h {self.cda.pg_host} -d {self.cda.pg_database} -U {self.cda.pg_username} -p {self.cda.pg_port} -a -q -f postgres_create_table_crashes.sql'
            , shell=True
            , stdout=subprocess.PIPE
            ) as proc:

            output = proc.stdout.read()

        end = time.perf_counter()
        seconds = (end-start)
        print(f'Copy to Postgres complete. Elapsed time: {seconds:0.1f} seconds')



    def run(self):

        current_timestamp = datetime.now(self.tz).strftime('%Y-%m-%d %H:%M:%S %Z')
        print(f'{current_timestamp} -> ', end='')

        if (self.remote_file_has_new_header()) or (self.args.force_refresh):
            self.download_file()

        if self.args.postgres:
            try:
                self.push_to_postgres()
            except Exception as e:
                print('Push to remote postgres server failed with this error:')
                print(e)
                return



if __name__ == '__main__':

    scd = SnapshotCrashData()
    scd.run()

