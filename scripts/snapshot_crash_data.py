# snapshot_crash_data.py

import pytz
import time
import requests
import pandas as pd
from datetime import datetime

from scripts.crash_data_analysis import CrashDataAnalysis


class SnapshotCrashData():

    def __init__(self):
        self.url = 'https://services1.arcgis.com/zdB7qR0BtYrg0Xpl/arcgis/rest/services/ODC_CRIME_TRAFFICACCIDENTS5YR_P/FeatureServer/325/query'
        self.page_size = 2000
        self.max_records_to_get = 50000
        self.seconds_to_wait = 5
        self.cda = CrashDataAnalysis()

    def get_latest_timestamp_utc(self):
        """Return the most recent reported_date in postgres as a UTC datetime, or None if table is empty/missing."""
        try:
            latest = self.cda.most_recent_crash_timestamp()
            if latest is None:
                return None
            return latest.astimezone(pytz.utc)
        except Exception:
            return None

    def fetch_new_records(self):
        """Fetch records from ArcGIS API newer than what's already in postgres."""

        latest_utc = self.get_latest_timestamp_utc()

        if latest_utc is not None:
            ts_str = latest_utc.strftime('%Y-%m-%d %H:%M:%S')
            where_statement = f"reported_date > timestamp '{ts_str}'"
            print(f'Fetching records after: {ts_str} UTC')
        else:
            where_statement = '1=1'
            print('No existing data found, fetching all records.')

        all_records = []
        offset = 0

        while True:
            params = {
                'where': where_statement,
                'outFields': '*',
                'resultRecordCount': self.page_size,
                'resultOffset': offset,
                'orderByFields': 'reported_date ASC',
                'f': 'json',
            }

            print(f'  Requesting offset {offset}...', end=' ')
            r = requests.get(self.url, params=params)
            r.raise_for_status()
            data = r.json()

            features = data.get('features', [])
            print(f'{len(features)} records.')

            if r.status_code != 200:
                print(f'API returned error code: {r.status_code}')
                print('Parameters:')
                print(params)
                print('Response:')
                print(r.text)
                break

            all_records.extend(f['attributes'] for f in features)

            if len(features) < self.page_size:
                break

            if len(all_records) >= self.max_records_to_get:
                break


            time.sleep(self.seconds_to_wait)

            offset += self.page_size

        if not all_records:
            print('No new records found.')
            return None

        df = pd.DataFrame(all_records)

        # ArcGIS returns dates as epoch milliseconds in Denver local time
        for col in ['reported_date', 'first_occurrence_date', 'last_occurrence_date']:
            if col in df.columns:
                df[col] = (
                    pd.to_datetime(df[col], unit='ms', utc=False)
                    .dt.tz_localize('America/Denver', ambiguous=True, nonexistent='shift_forward')
                    .dt.tz_convert('UTC')
                    )

        df['updated_at'] = datetime.now(pytz.timezone('UTC'))

        print(f'Total new records: {len(df):,}')
        return df

    def run(self):
        print()
        df = self.fetch_new_records()

        if df is None:
            return

        df_preprocessed = self.cda.preprocess_crash_data(df=df, verbose=True, all_columns=False)
        self.cda.upsert_crashes(df_preprocessed)


if __name__ == '__main__':
    scd = SnapshotCrashData()
    scd.run()
