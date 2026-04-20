DROP TABLE IF EXISTS crashes;

CREATE TABLE "crashes" (
  "row_id" BIGSERIAL PRIMARY KEY
  , "incident_id" CHARACTER VARYING(20) NOT NULL UNIQUE
  , "top_traffic_accident_offense" CHARACTER VARYING(100)
  , "reported_date" TIMESTAMP WITH TIME ZONE
  , "incident_address_corrected" CHARACTER VARYING(200)
  , "at_freeway" BOOL
  , "geo_lon" DOUBLE PRECISION
  , "geo_lat" DOUBLE PRECISION
  , "neighborhood_id" CHARACTER VARYING(100)
  , "bicycle_ind" DOUBLE PRECISION
  , "pedestrian_ind" DOUBLE PRECISION
  , "day_or_night" CHARACTER VARYING(10)
  , "driver_action" CHARACTER VARYING(100)
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
);

CREATE INDEX crashes_geom_gist ON crashes USING gist (geom);
