-- postgres_add_denver_geom.sql

ALTER TABLE street_routes ADD COLUMN geom_denver GEOMETRY;
UPDATE street_routes SET geom_denver = ST_Transform(geom,3502);
CREATE INDEX street_routes_geom_denver_gist ON street_routes USING gist(geom_denver);

