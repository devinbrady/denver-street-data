

-- Crashes that occurred within 0.05 mile distance of the given latitude and longitude

select
*
, ST_Distance(
    geom_denver, ST_Transform(ST_SetSRID(ST_MakePoint({lat_lon[1]},{lat_lon[0]}), 4326), 3502)
) as distance_feet

from crashes

where geo_lon is not null
and ST_Distance(geom_denver, ST_Transform(ST_SetSRID(ST_MakePoint({lat_lon[1]},{lat_lon[0]}), 4326), 3502)) < 264

order by reported_date
;



-- Percentage of crashes that lack a lat/lon. varies between 3-5% each year

select
to_char(reported_date, 'YYYY') as yr
, count(*) as crashes
, sum(case when geom is null then 1 else 0 end) as null_geom
, 1.0 * sum(case when geom is null then 1 else 0 end) / count(*) as perc
from crashes
group by 1 order by 1
;


-- Find the neighborhood of a lat/lon

select nbhd_name

from statistical_neighborhoods sn

where ST_Intersects(
    ST_SetSRID(ST_MakePoint(-104.963117, 39.744474), 4326)
    , sn.geom
)
;


-- Timezone conversion example

select
incident_id
, reported_date
, reported_date at time zone 'America/Denver'

from crashes

order by reported_date desc

limit 8



-- Count of days between two dates

select date_part('day', max(reported_date) - min(reported_date)) from crashes
;