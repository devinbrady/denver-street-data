
import os
import pytz
import hashlib
import numpy as np
import pandas as pd
import geopy.distance
import geopandas as gpd
from datetime import datetime
import matplotlib.pyplot as plt
from shapely.geometry import Point


class CrashDataAnalysis():

    def __init__(self):
        pass



    def crash_dataframe(self, csv_file=None, verbose=False):
        """
        Wrapper for read_and_preprocess_crash_data()
        """

        if not csv_file:
            csv_file = self.most_recent_file()

        return self.read_and_preprocess_crash_data(csv_file, verbose=verbose)



    def read_and_preprocess_crash_data(self, csv_file, verbose=False):
        """
        Read in the most recent CSV file of crash data and return a cleaned DataFrame
        """

        if verbose:
            print(f'Reading file: {csv_file}')
        
        df = pd.read_csv(csv_file, low_memory=False)

        # There's one bad row with a NULL incident_id
        df = df[df.incident_id.notnull()].copy()

        df['incident_id'] = df['incident_id'].astype(int)

        df['sbi'] = df['top_traffic_accident_offense'].str.contains('SBI')
        df['fatality'] = df['top_traffic_accident_offense'].str.contains('FATAL')
        df['sbi_or_fatality'] = (df['sbi']) | (df['fatality'])

        date_fields = [c for c in df.columns if '_date' in c.lower()]

        for d in date_fields:
            df[d] = pd.to_datetime(df[d])

        date_field_name = 'reported_date'
        df['crash_date_str'] = df[date_field_name].dt.strftime('%Y-%m-%d %a')
        df['crash_time_str'] = df[date_field_name].dt.strftime('%a %b %-d, %-I:%M %p')
        df['crash_year'] = df[date_field_name].dt.year
        df['crash_day_of_year'] = df[date_field_name].dt.day_of_year
        df['one'] = 1
        df = df.sort_values(by=date_field_name)

        df.drop(columns='shape', inplace=True)

        if verbose:
            print(f'Max timestamp: {df[date_field_name].max()}')

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



    def recent_fatality_crashes(self, df):

        f = df[df.fatality].copy()
        f['days_between'] = (f['reported_date'] - f['reported_date'].shift(1)).dt.total_seconds() / 60 / 60 / 24

        tz = pytz.timezone('America/Denver')
        denver_timestamp = datetime.now(tz)

        f['reported_date_tz'] = f['reported_date'].dt.tz_localize(tz)
        f['days_ago'] = (denver_timestamp - f['reported_date_tz']).dt.total_seconds() / 60 / 60 / 24

        recent_f = f.tail(20)
        print(recent_f[['incident_address', 'neighborhood_id', 'crash_time_str', 'days_between', 'days_ago']].to_string(index=False))

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



    def crashes_near_point(self, df, lat, lon, radius_miles=1):
        """
        Return a subset of the crash dataframe where the crashes occured near a point
        """

        df['target_lat'] = lat
        df['target_lon'] = lon

        df['distance_miles'] = self.pythagorean_distance(df['geo_lat'], df['geo_lon'], df['target_lat'], df['target_lon'])

        recent = df[df['distance_miles'] < radius_miles].tail(20)
        print(recent[['incident_address', 'distance_miles', 'crash_time_str', 'top_traffic_accident_offense']].to_string(index=False))

        return df


