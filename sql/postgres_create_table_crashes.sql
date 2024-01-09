DROP TABLE IF EXISTS crashes;

CREATE TABLE "crashes" (
    "incident_id" BIGINT NOT NULL
    , "top_traffic_accident_offense" CHARACTER VARYING(100)
    , "reported_date" TIMESTAMP WITH TIME ZONE
    , "incident_address_corrected" CHARACTER VARYING(100)
    , "at_freeway" BOOL
    , "geo_lon" DOUBLE PRECISION
    , "geo_lat" DOUBLE PRECISION
    , "neighborhood_id" CHARACTER VARYING(100)
    , "bicycle_ind" DOUBLE PRECISION
    , "pedestrian_ind" DOUBLE PRECISION
    , "day_or_night" CHARACTER VARYING(10)
    , "updated_at" TIMESTAMP WITH TIME ZONE
    , "sbi" BOOL
    , "fatality" BOOL
    , "sbi_or_fatality" BOOL
    , "crash_date" CHARACTER VARYING(100)
    , "crash_date_str" CHARACTER VARYING(100)
    , "crash_time_str" CHARACTER VARYING(100)
    , "crash_year" INTEGER
    , "crash_day_of_year" INTEGER
    , "geom" GEOMETRY
    , "geom_denver" GEOMETRY
    , CONSTRAINT incident_id_pkey PRIMARY KEY (incident_id)
);

CREATE INDEX crashes_geom_gist
  ON crashes
  USING gist
  (geom)
  ;

\copy crashes(incident_id,top_traffic_accident_offense,reported_date,incident_address_corrected,at_freeway,geo_lon,geo_lat,neighborhood_id,bicycle_ind,pedestrian_ind,day_or_night,updated_at,sbi,fatality,sbi_or_fatality,crash_date,crash_date_str,crash_time_str,crash_year,crash_day_of_year) FROM '/Users/devin/Projects/denver-street-data/data/crash_data_preprocessed.csv' DELIMITERS ',' CSV HEADER;


UPDATE crashes SET geom = ST_GeomFromText('POINT(' || geo_lon || ' ' || geo_lat || ')',4326);
UPDATE crashes SET geom_denver = ST_Transform(geom,3502);
CREATE INDEX crashes_geom_denver_gist ON crashes USING gist(geom_denver);

ANALYZE crashes;
