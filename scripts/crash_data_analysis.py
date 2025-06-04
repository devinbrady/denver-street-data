
import os
import sys
import pytz
import hashlib
import geocoder
import numpy as np
import pandas as pd
import psycopg2 as pg
import geopy.distance
import geopandas as gpd
from pathlib import Path
from datetime import datetime
import matplotlib.pyplot as plt
from shapely.geometry import Point
from sqlalchemy import create_engine



class CrashDataAnalysis():

    def __init__(self):
        
        self.pg_host = os.environ['PGHOST']
        self.pg_database = os.environ['PGDATABASE']
        self.pg_username = os.environ['PGUSERNAME']
        self.pg_port = os.environ['PGPORT']
        self.pg_password = os.environ['PGPASSWORD']
        
        postgres_connected = False
        try:
            conn_postgres = self.connect_to_postgres()
            postgres_connected = True
        except Exception as e:
            print(e)
            print('No postgres connection.')

        if postgres_connected:
            self.conn = conn_postgres
        else:
            self.conn = None

        self.local_timezone = pytz.timezone('America/Denver')

        self.crash_table_fields = [
            'incident_id'
            , 'top_traffic_accident_offense'
            , 'reported_date'
            , 'incident_address_corrected'
            , 'at_freeway'
            , 'geo_lon'
            , 'geo_lat'
            , 'neighborhood_id'
            , 'bicycle_ind'
            , 'pedestrian_ind'
            , 'day_or_night'
            , 'driver_action'
            , 'updated_at'
            , 'sbi'
            , 'fatality'
            , 'sbi_or_fatality'
            , 'crash_date'
            , 'crash_date_str'
            , 'crash_time_str'
            , 'crash_year'
            , 'crash_day_of_year'
        ]

        self.files = {}
        self.files['crash_data_raw'] = Path('data/crash_data_raw.csv')

        

    def connect_to_postgres(self):

        # conn = pg.connect(f"host={self.pg_host} dbname={self.pg_database} user={self.pg_username} password={self.pg_password}")

        conn = create_engine(f'postgresql+psycopg2://{self.pg_username}:{self.pg_password}@{self.pg_host}:{self.pg_port}/{self.pg_database}')

        return conn



    def most_recent_crash_timestamp(self):
        """Return timestamp in local time showing the most recent crash in the dataset"""

        return pd.to_datetime(
            pd.read_sql('select max(reported_date) from crashes', self.conn).iloc[0].values[0]
        ).tz_localize('UTC').tz_convert('America/Denver')



    def crash_dataframe(self):
        """
        Return DataFrame with all crashes and all fields
        """

        df = pd.read_csv(self.files['crash_data_raw'], low_memory=False)

        df_preprocessed = self.preprocess_crash_data(df=df, verbose=False, all_columns=True)

        return df_preprocessed



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
            , 'LIGHT_CONDITION'
            , 'TU1_DRIVER_ACTION'
            , 'TU2_DRIVER_ACTION'
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
            df[d] = pd.to_datetime(df[d], format='mixed')

        date_field_name = 'reported_date'

        # In the raw data, reported_date is in local Denver time. Convert to UTC and store in the database as UTC.

        # todo: sqlite/pandas seems to read this tz-ambiguous field in the local timezone
        # when I switch this to postgres, might have to be more explicit about timezones
        
        if df[date_field_name].dt.tz is None:
            print(f'Converting field "{date_field_name}" to Denver time.')
            df[date_field_name] = df[date_field_name].dt.tz_localize(
                    self.local_timezone
                    , ambiguous=True
                    , nonexistent='shift_forward'
                    )

        df = self.incident_address_cleanup(df)

        df['day_or_night'] = df.LIGHT_CONDITION.map({
            '  ': 'Unknown'
            , 'DARK-LIGHTED': 'Night'
            , 'DARK-UNLIGHTED': 'Night'
            , 'DAWN OR DUSK': 'Night'
            , 'DAY LIGHT': 'Day'
            , 'Dark-Lighted': 'Night'
            , 'Dark-Unlighted': 'Night'
            , 'Dawn or Dusk': 'Night'
            , 'Daylight': 'Day'
            , 'UNDER INVESTIGATION': 'Unknown'
        })

        df['driver_action'] = (
            'TU1: ' + df['TU1_DRIVER_ACTION'].str.lower().str.strip()
            + ', TU2: ' + df['TU2_DRIVER_ACTION'].str.lower().str.strip()
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

        if all_columns:
            return_columns = df.columns
        else:
            return_columns = self.crash_table_fields
        
        return df[return_columns]



    def incident_address_cleanup(self, df):
        """
        Clean up the incident address field, add at_freeway flag
        """

        incident_mapping = {
            'N BIGHTON BLVD': 'N BRIGHTON BLVD'
            , 'I25 HWYNB': 'INTERSTATE 25'
            , 'I25 HWYSB': 'INTERSTATE 25'
            , 'I25HWY': 'INTERSTATE 25'
            , 'I70 HWYWB': 'INTERSTATE 70'
            , 'I70 HWYEB': 'INTERSTATE 70'
            , 'I225 HWYNB': 'INTERSTATE 225'
            , 'I225 HWYSB': 'INTERSTATE 225'
            , 'W 6TH AVE': 'W 6TH AVENUE FWY'
            , 'PARK AVEW': 'PARK AVE W'
            , 'S MONACO ST': 'S MONACO STREET PKWY'
            , 'N MONACO ST': 'N MONACO STREET PKWY'
            , 'E MLK BLVD': 'E MARTIN LUTHER KING BLVD'
            , 'E MARTIN LUTHER KING BLVD': 'E MARTIN LUTHER KING JR BLVD'
            , 'E GVR BLVD': 'GREEN VALLEY RANCH BLVD'
        }

        df['incident_address_corrected'] = df.incident_address.replace(incident_mapping, regex=True)

        freeways = [
            'INTERSTATE 25'
            , 'INTERSTATE 70'
            , 'INTERSTATE 225'
            , 'W 6TH AVENUE FWY'
            , 'PENA BLVD'
        ]

        df['at_freeway'] = False

        for f in freeways:
            df.loc[df.incident_address_corrected.str.contains(f), 'at_freeway'] = True

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



    def recent_deadly_crashes(self, additional_columns=None):
        """
        Return dataframe with info about recent deadly crashes
        """

        columns_to_query = ['incident_address_corrected', 'neighborhood_id', 'crash_time_str', 'pedestrian_ind', 'bicycle_ind']

        if additional_columns:
            columns_to_query += additional_columns

        
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

        columns_to_print = ['crash_time_str', 'pedestrian', 'bicycle', 'incident_address_corrected', 'neighborhood_id']
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



    def days_between_crashes_near_point(self, lat, lon, radius_miles=0.25):
        """
        Return a count of days between crashes that have occurred near a point
        """

        query = f"""
            select
            count(*) as num_crashes

            from crashes

            where geo_lon is not null
            and ST_Distance(
                geom_denver, ST_Transform(ST_SetSRID(ST_MakePoint({lon},{lat}), 4326), 3502)
                ) < {radius_miles * 5280}

        """

        result = pd.read_sql(query, self.conn)
        num_crashes = result['num_crashes'].values[0]
        if num_crashes == 0:
            return None

        days_query = "select date_part('day', max(reported_date) - min(reported_date)) as days_in_data from crashes"
        days_result = pd.read_sql(days_query, self.conn)
        days_in_data = days_result['days_in_data'].values[0]

        return days_in_data / num_crashes



    def denver_timestamp(self):

        return datetime.now(tz=pytz.timezone('America/Denver'))



    def street_metrics(self, start_date, end_date):
        """
        Return metrics for the most dangerous streets in a time period
        """

        query = f"""
        with route_centerline_count as (
            select
            sr.gid
            , sr.lrsroute
            , sc.fullname
            , case when left(sc.fullname, 2) in ('N ', 'S ', 'E ', 'W ') then right(sc.fullname, length(sc.fullname)-2) else sc.fullname end as street_name_no_cardinal
            , row_number() over (partition by sr.gid, sr.lrsroute order by count(distinct sc.masterid) desc) 
                as fullname_priority

            from street_routes sr
            inner join street_centerline sc using (lrsroute)

            group by 1,2,3
        )

        , crashes_routes as (
            select distinct

            -- Speer Blvd has two different centerlines: 3900 for north and 3901 for south. These overlap at a lot of intersections,
            -- especially in the northern parts, which double-counts crashes, one for each centerline.
            -- Alias all of the southbound 3901 crashes as northbound 3900 crashes, then dedupe this, for analysis.
            -- See Speer_Blvd.ipynb for the map.

            case
                when sr.gid = 3901 then 3900 -- Speer north
                when sr.gid = 1453 then 1452 -- Speer south
                when sr.gid = 6167 then 6166 -- Marion Parkway

                else sr.gid end
                as gid

            , c.incident_id
            , c.sbi
            , c.fatality
            , c.sbi_or_fatality
            , c.bicycle_ind
            , c.pedestrian_ind

            from street_routes sr
            inner join crashes c on st_dwithin(sr.geom_denver, c.geom_denver, 25)

            where reported_date at time zone 'America/Denver' > '{start_date.strftime('%Y-%m-%d')}'
            and reported_date at time zone 'America/Denver' < '{end_date.strftime('%Y-%m-%d')}'
            and not at_freeway
        )

        , count_routes as (
            select
            cr.gid
            , sr1.lrsroute
            , st_length(sr1.geom_denver) / 5280 as length_miles
            , st_AsGeoJSON(sr1.geom) as street_line
            , count(cr.incident_id) as num_crashes
            , sum(cr.sbi::int) as num_sbi
            , sum(cr.fatality::int) as num_fatality
            , sum(cr.sbi_or_fatality::int) as num_sbi_or_fatality
            , sum(cr.bicycle_ind) as sum_bicycle_ind
            , sum(cr.pedestrian_ind) as sum_pedestrian_ind
            
            from crashes_routes cr
            inner join street_routes sr1 using (gid)
            
            group by 1,2,3,4
        )

        select
        count_routes.gid
        , count_routes.lrsroute
        , rcc.fullname
        , rcc.street_name_no_cardinal
        , count_routes.length_miles
        , count_routes.street_line
        , count_routes.num_crashes
        , count_routes.num_sbi
        , count_routes.num_fatality
        , count_routes.num_sbi_or_fatality
        , count_routes.sum_bicycle_ind
        , count_routes.sum_pedestrian_ind

        from count_routes
        inner join route_centerline_count rcc on (rcc.gid = count_routes.gid and rcc.fullname_priority = 1)
        """

        street_crashes = pd.read_sql(query, self.conn)
        
        days_in_data = (end_date - start_date).days
        street_crashes['days_in_data'] = days_in_data

        street_crashes = street_crashes[street_crashes.length_miles > 0.5].copy()
        street_crashes['days_between_crashes'] = days_in_data / street_crashes['num_crashes']
        street_crashes['crashes_per_mile_per_week'] = ((street_crashes['num_crashes'] / street_crashes['length_miles']) / (days_in_data/7))
        street_crashes['pedestrian_ind_per_mile_per_year'] = ((street_crashes['sum_pedestrian_ind'] / street_crashes['length_miles']) / (days_in_data/365.25))

        return street_crashes.sort_values(by='crashes_per_mile_per_week', ascending=False)



    def geocode_location(self, location_str):

        gc = geocoder.google(location_str)

        if not gc.ok:
            raise Exception(f'Google Geocoder failed, message: {gc.status}')

        if gc.json['confidence'] < 9:
            raise Exception(f"Geocoder confidence is too low for location: \"{location_str}\", confidence {gc.json['confidence']}")

        return gc.latlng




