with street_crashes as (
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
    , c.reported_date
    , c.sbi
    , c.fatality
    , c.sbi_or_fatality

    from street_routes sr
    inner join crashes c on st_dwithin(sr.geom_denver, c.geom_denver, 25)

    where c.reported_date at time zone 'America/Denver' > '2020-07-01'
    and not c.at_freeway
)

, crash_count as (
    select
    sc.gid
    , year_month(sc.reported_date)
    , count(*) as num_crashes
    , sum(cr.sbi) as num_sbi
    , sum(cr.fatality) as num_fatalities
    , sum(cr.sbi_or_fatality) as num_sbi_or_fatalities

    from street_crashes sc

    group by 1,2
    order by 1,2
)

, crash_median as (
    select
    cc.gid
    , median(num_crashes) as median_crashes
    , median(num_sbi) as median_sbi
    , median(num_fatalities) as median_fatalities
    , median(num_sbi_or_fatalities) as median_sbi_or_fatalities

    from crash_count cc
)

select
cc.*
, cm.*
, cc.num_crashes - cm.median_crashes as crashes_diff_from_median

from crash_count cc
inner join crash_median cm using (gid)