-- postgres_add_denver_geom.sql

ALTER TABLE street_routes ADD COLUMN geom_denver GEOMETRY;
UPDATE street_routes SET geom_denver = ST_Transform(geom,3502);
CREATE INDEX street_routes_geom_denver_gist ON street_routes USING gist(geom_denver);

ALTER TABLE street_centerline ADD COLUMN geom_denver GEOMETRY;
UPDATE street_centerline SET geom_denver = ST_Transform(geom,3502);
CREATE INDEX street_centerline_geom_denver_gist ON street_centerline USING gist(geom_denver);
