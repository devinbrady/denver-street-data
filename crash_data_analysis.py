
import os
import pytz
import hashlib
import numpy as np
import pandas as pd
import sqlite3 as sq
import psycopg2 as pg
import geopy.distance
import geopandas as gpd
from datetime import datetime
import matplotlib.pyplot as plt
from shapely.geometry import Point


class CrashDataAnalysis():

    def __init__(self):
        
        conn_sqlite = sq.connect('data/denver_crashes.sqlite')
        
        postgres_connected = False
        try:
            conn_postgres = self.connect_to_postgres()
            postgres_connected = True
        except:
            print('No postgres connection.')

        if postgres_connected:
            self.conn = conn_postgres
        else:
            self.conn = conn_sqlite

        self.local_timezone = pytz.timezone('America/Denver')


    def connect_to_postgres(self):

        pg_host = os.environ['PGHOST']
        pg_database = os.environ['PGDATABASE']
        pg_username = os.environ['PGUSERNAME']
        pg_port = os.environ['PGPORT']
        pg_password = os.environ['PGPASSWORD']

        conn = pg.connect(f"host={pg_host} dbname={pg_database} user={pg_username} password={pg_password}")

        return conn



    def crash_dataframe(self, csv_file=None, verbose=False, all_columns=False):
        """
        Wrapper for preprocess_crash_data()
        """

        df = self.read_crash_data(verbose)

        return self.preprocess_crash_data(df, verbose=verbose, all_columns=all_columns)



    def read_crash_data(self, verbose=False):

        if verbose:
            print(f'Reading file: data/denver_crashes.sqlite')
        
        df = pd.read_sql('select * from crashes_raw', self.conn)

        return df



    def preprocess_crash_data(self, df, verbose=False, all_columns=False):
        """
        Read in the most recent CSV file of crash data and return a cleaned DataFrame
        """
        
        columns_to_read = [
            'incident_id'
            , 'top_traffic_accident_offense'
            , 'reported_date'
            , 'incident_address'
            , 'geo_lon'
            , 'geo_lat'
            , 'neighborhood_id'
            , 'bicycle_ind'
            , 'pedestrian_ind'
            # , 'SERIOUSLY_INJURED'
            # , 'FATALITIES'
            , 'updated_at'
        ]

        if not all_columns:
            df = df[columns_to_read].copy()

        df['bicycle_ind'] = df['bicycle_ind'].fillna(0)
        df['pedestrian_ind'] = df['pedestrian_ind'].fillna(0)

        # Manually add a crash that is not yet reflected in the database
        # crash_to_add = pd.DataFrame({
        #     'top_traffic_accident_offense': 'FATAL'
        #     , 'reported_date': '2022-05-17 22:00:00'
        #     , 'incident_id': '999'
        # }, index=[0])
        # df = pd.concat([df, crash_to_add], ignore_index=True)


        # There's one bad row with a NULL incident_id
        df = df[df.incident_id.notnull()].copy()

        df['incident_id'] = df['incident_id'].astype(int)

        df['sbi'] = df['top_traffic_accident_offense'].str.contains('SBI')
        df['fatality'] = df['top_traffic_accident_offense'].str.contains('FATAL')
        df['sbi_or_fatality'] = (df['sbi']) | (df['fatality'])

        date_fields = [c for c in df.columns if '_date' in c.lower()] + ['updated_at']

        for d in date_fields:
            df[d] = pd.to_datetime(df[d])

        date_field_name = 'reported_date'
        # todo: sqlite/pandas seems to read this tz-ambiguous field in the local timezone
        # when I switch this to postgres, might have to be more explicit about timezones
        df[date_field_name] = df[date_field_name].dt.tz_localize(
                self.local_timezone
                , ambiguous=True
                , nonexistent='shift_forward'
                )

        df['crash_date'] = df[date_field_name].dt.strftime('%Y-%m-%d')
        df['crash_date_str'] = df[date_field_name].dt.strftime('%Y-%m-%d %a')
        # df['crash_month_day'] = df[date_field_name].dt.strftime('%m-%d')
        df['crash_time_str'] = df[date_field_name].dt.strftime('%a %b %-d, %-I:%M %p')
        df['crash_year'] = df[date_field_name].dt.year
        df['crash_day_of_year'] = df[date_field_name].dt.day_of_year
        df = df.sort_values(by=date_field_name)

        df.drop_duplicates(subset=['incident_id'], inplace=True)

        if verbose:

            updated_at = df['updated_at'].dt.tz_convert(self.local_timezone).max()
            updated_at_str = updated_at.strftime('%a %b %-d, %-I:%M %p')
            print(f'Local database updated at: {updated_at_str}')

            max_timestamp = df[date_field_name].max()
            max_timestamp_str = max_timestamp.strftime('%a %b %-d, %-I:%M %p')

            days_ago = (self.denver_timestamp() - max_timestamp).total_seconds() / 60 / 60 / 24

            print(f'Max timestamp in database: {max_timestamp_str} ({days_ago:.2f} days ago)')

            this_year_deadly_crashes = df[df.crash_year == self.denver_timestamp().year].fatality.sum()
            print(f'Deadly crashes this year: {this_year_deadly_crashes}')

        return df



    def crash_counts_aggregate(self, df, groupby_field):
        """
        Aggregate crash counts by a specified groupby_field
        """

        return df.groupby(groupby_field).agg(
            crashes=('incident_id', 'size')
            # , bicycle_ind=('bicycle_ind', 'sum')
            # , pedestrian_ind=('pedestrian_ind', 'sum')
            , sbi=('sbi', 'sum')
            , fatalities=('fatality', 'sum')
            )



    def list_all_files(self):
        """
        Return list of all files in the data directory
        """

        return sorted(['data/' + f for f in os.listdir('data/') if '.csv' in f])



    def most_recent_file(self):
        """
        Return the name of the most recent file
        """

        return self.list_all_files()[-1]



    def recent_deadly_crashes(self):
        """
        Return dataframe with info about recent deadly crashes
        """

        columns_to_query = ['incident_address', 'neighborhood_id', 'crash_time_str', 'pedestrian_ind', 'bicycle_ind']
        
        query = f"""
            select
            reported_date,
            {','.join(columns_to_query)}
            from crashes

            where fatality

            order by reported_date
        """

        f = pd.read_sql(query, self.conn)

        f['pedestrian'] = f['pedestrian_ind'].apply(lambda row: '' if row == 0 else 'x')
        f['bicycle'] = f['bicycle_ind'].apply(lambda row: '' if row == 0 else 'x')

        # f['reported_date'] = pd.to_datetime(f['reported_date'])
        
        # f['days_between'] = (f['reported_date'] - f['reported_date'].shift(1)).dt.total_seconds() / 60 / 60 / 24

        # f['now'] = self.denver_timestamp()
        # f['days_ago'] = f['now'] - f['reported_date']
        # print(f['reported_date'])
        # f['days_ago'] = (self.denver_timestamp() - f['reported_date']).dt.total_seconds() / 60 / 60 / 24

        recent_f = f.tail(20)

        columns_to_print = ['crash_time_str', 'pedestrian', 'bicycle', 'incident_address', 'neighborhood_id']
        # print(recent_f[columns_to_print].to_string(index=False))

        return f



    def pythagorean_distance(self, lat1, lon1, lat2, lon2):
        """
        Pythagorean formula. Assumes Earth is flat, within counties. Not exact but close enough
        Why use this? Doing math on whole dataframe columns is fast
        """

        length_of_lat_degree_in_miles, length_of_lon_degree_in_miles = self.lat_long_miles(lat1.median())
        
        distance_in_miles = np.sqrt(
            np.square((lat1 - lat2) * length_of_lat_degree_in_miles) 
            + np.square((lon1 - lon2) * length_of_lon_degree_in_miles)
            )

        return distance_in_miles



    def lat_long_miles(self, lat):
        """
        Calculate the length of a degree of latitude and longitude in miles
        In terms of miles, a degree of longitude in Reno is slightly less than a degree of longitude in Las Vegas
        source: http://www.csgnetwork.com/degreelenllavcalc.html
        """

        lat = self.deg2rad(lat)

        m1 = 111132.92      # latitude calculation term 1
        m2 = -559.82        # latitude calculation term 2
        m3 = 1.175          # latitude calculation term 3
        m4 = -0.0023        # latitude calculation term 4
        p1 = 111412.84      # longitude calculation term 1
        p2 = -93.5          # longitude calculation term 2
        p3 = 0.118          # longitude calculation term 3
        one_meter_in_miles = 0.000621371

        latlen = m1 + (m2 * np.cos(2 * lat)) + (m3 * np.cos(4 * lat)) + (m4 * np.cos(6 * lat))
        longlen = (p1 * np.cos(lat)) + (p2 * np.cos(3 * lat)) + (p3 * np.cos(5 * lat))

        miles = np.asarray([latlen, longlen]) * one_meter_in_miles

        return miles



    def deg2rad(self, deg):
        """
        Convert degrees to radians
        """

        conv_factor = (2.0 * np.pi)/360.0
        return deg * conv_factor



    def crashes_near_point(self, df, lat, lon, radius_miles=1, verbose=False):
        """
        Return a subset of the crash dataframe where the crashes occured near a point
        """

        df = df.copy()

        df['target_lat'] = lat
        df['target_lon'] = lon

        df['distance_miles'] = self.pythagorean_distance(df['geo_lat'], df['geo_lon'], df['target_lat'], df['target_lon'])

        recent = df[df['distance_miles'] < radius_miles]

        if verbose:
            print(recent[['incident_address', 'distance_miles', 'crash_time_str', 'top_traffic_accident_offense']].to_string(index=False))

        return recent



    def denver_timestamp(self):

        return datetime.now(tz=pytz.timezone('America/Denver'))


