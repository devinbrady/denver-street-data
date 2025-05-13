# snapshot_crash_data.py

import os
import pytz
import time
import shutil
import string
import random
import hashlib
import argparse
import requests
import subprocess
import pandas as pd
from pathlib import Path
from datetime import datetime

from crash_data_analysis import CrashDataAnalysis



class SnapshotCrashData():

    def __init__(self):

        # Hard code an input CSV
        self.input_file = Path('../data/crash_data_raw_20250502.csv')
        # self.input_file = None

        parser = argparse.ArgumentParser()
        parser.add_argument('-f', '--download-force', action='store_true', help='Download a copy even if the remote header has not changed')
        parser.add_argument('-p', '--postgres-force', action='store_true', help='Preprocess the local raw file and upload to postgres')
        self.args = parser.parse_args()

        self.files = {}
        self.files['header_etag'] = Path('../data/header_etag_source.txt')
        self.files['hash_local'] = Path('../data/data_hash_local.txt')
        self.files['hash_postgres'] = Path('../data/data_hash_postgres.txt')
        self.files['crash_data_raw'] = Path('../data/crash_data_raw.csv')
        self.files['crash_data_preprocessed'] = Path('../data/crash_data_preprocessed.csv')

        for file_key in list(self.files.keys()):
            if not self.files[file_key].exists():
                with open(self.files[file_key], 'w') as f:
                    f.write(''.join(random.choices(string.ascii_lowercase, k=13)))

        # self.url = 'https://www.denvergov.org/media/gis/DataCatalog/traffic_accidents/csv/traffic_accidents.csv'
        self.url = 'https://services1.arcgis.com/zdB7qR0BtYrg0Xpl/arcgis/rest/services/ODC_CRIME_TRAFFICACCIDENTS5YR_P/FeatureServer/325/query?outFields=*&where=1%3D1&f=geojson'

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

        with open(self.files['header_etag'], 'r') as f:
            old_header_etag = f.read()

        try:
            r = requests.head(self.url)
        except Exception as e:
            print('Something went wrong accessing the remote file, so we will not try to download it.')
            return False
        
        # print('headers:')
        # for k in r.headers:
        #     print(k)
        #     print(r.headers[k])
        #     print()

        # self.remote_header_etag = r.headers['ETag']
        self.remote_header_etag = str(random.random()) # force the download to happen every time

        if self.remote_header_etag == old_header_etag:
            print('Source data matches local data.')

        return self.remote_header_etag != old_header_etag
        


    def postgres_push_needed(self):
        """
        Return True if the local hash differs from what has previously been pushed to postgres
        """

        with open(self.files['hash_local'], 'r') as f:
            hash_local = f.read()

        with open(self.files['hash_postgres'], 'r') as f:
            hash_postgres = f.read()

        if hash_local == hash_postgres:
            print('Local data matches postgres data.')

        return hash_local != hash_postgres



    def write_new_etag_to_file(self):
        """Write the ETag from the remote header file to the local text file"""

        with open(self.files['header_etag'], 'w') as f:
            f.write(self.remote_header_etag)



    def save_new_data_hash(self, df, file_path):
        """
        Save a hash of a dataframe to a file
        """

        df_hash = hashlib.sha256(pd.util.hash_pandas_object(df).values).hexdigest()

        with open(file_path, 'w') as f:
            f.write(df_hash)



    def download_file(self):


        if self.input_file:
            print(f'Reading: {self.input_file}')
            df = pd.read_csv(self.input_file, low_memory=False)
        
        else:

            # Download
            print('Downloading data from denvergov... ', end='')

            try:
                df = gpd.read_file(self.url, low_memory=False)
            except Exception as e:
                print('Something went wrong trying to download the source data. Quitting.')
                return

            print('complete.')


        df['updated_at'] = datetime.now(pytz.timezone('UTC')).isoformat()

        df.to_csv(self.files['crash_data_raw'], index=False)
        print(f"Raw data saved to: {self.files['crash_data_raw']}")

        df_preprocessed = self.cda.preprocess_crash_data(df=df, verbose=False, all_columns=False)

        df_preprocessed.to_csv(self.files['crash_data_preprocessed'], index=False)
        print(f"Preprocessed data saved to: {self.files['crash_data_preprocessed']}")

        number_of_crashes = len(df)
        print(f'Crashes in dataset: {number_of_crashes:,}')
        print(f'Oldest crash: {df_preprocessed.reported_date.min()}')
        print(f'Most recent crash: {df_preprocessed.reported_date.max()}')

        self.write_new_etag_to_file()
        self.save_new_data_hash(df_preprocessed[[c for c in df_preprocessed.columns if c != 'updated_at']], self.files['hash_local'])



    def push_to_postgres(self):
        """
        Push the most recent local data to Postgres
        """

        start = time.perf_counter()

        with subprocess.Popen(
            f'psql -h {self.cda.pg_host} -d {self.cda.pg_database} -U {self.cda.pg_username} -p {self.cda.pg_port} -a -q -f ../sql/postgres_create_table_crashes.sql'
            , shell=True
            , stdout=subprocess.PIPE
            ) as proc:

            output = proc.stdout.read()

        shutil.copyfile(self.files['hash_local'], self.files['hash_postgres'])

        end = time.perf_counter()
        seconds = (end-start)
        print(f'Copy to Postgres complete. Elapsed time: {seconds:0.1f} seconds')



    def run(self):

        # current_timestamp = datetime.now(self.tz).strftime('%Y-%m-%d %H:%M:%S %Z')
        # print(f'{current_timestamp} -> ', end='')

        if (self.remote_file_has_new_header()) or (self.args.download_force):
            self.download_file()

        if (self.postgres_push_needed() or self.args.postgres_force):
            try:
                self.push_to_postgres()
            except Exception as e:
                print('Push to remote postgres server failed with this error:')
                print(e)
                return



if __name__ == '__main__':

    scd = SnapshotCrashData()
    scd.run()

