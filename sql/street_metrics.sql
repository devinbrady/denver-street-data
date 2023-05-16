with route_centerline_count as (
    select
    sr.gid
    , sr.lrsroute
    , sc.fullname
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
    
    from crashes_routes cr
    inner join street_routes sr1 using (gid)
    
    group by 1,2,3,4
)

select
count_routes.gid
, count_routes.lrsroute
, rcc.fullname
, count_routes.length_miles
, count_routes.street_line
, count_routes.num_crashes
, count_routes.num_sbi
, count_routes.num_fatality
, count_routes.num_sbi_or_fatality

from count_routes
inner join route_centerline_count rcc on (rcc.gid = count_routes.gid and rcc.fullname_priority = 1)