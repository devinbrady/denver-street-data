# New Server Provisioning

1. Create the new Postgres server cluster on Crunchybridge (this can take about 10 minutes to be created)
2. Generate superuser login creds
3. Add login creds to terminal profile
3. Log into the server using psql

        psql -h "$PGHOST" -d "$PGDATABASE" -U "$PGUSERNAME" -p "$PGPORT"

4. Install PostGIS on new Postgres cluster

        SET SESSION pgaudit.log = 'none';
        CREATE EXTENSION postgis;
        SET SESSION pgaudit.log = 'all';

6. Load crash data (this initial load also takes about 10 minutes)

        python snapshot_crash_data.py -p

7. Load the shapefiles. The centerlines table takes at least 15 minutes.

        shp2pgsql -s 4326 -I shapefiles/street_routes/street_routes.shp | psql -h "$PGHOST" -d "$PGDATABASE" -U "$PGUSERNAME" -p "$PGPORT"
        shp2pgsql -s 4326 -I shapefiles/street_centerline/street_centerline.shp | psql -h "$PGHOST" -d "$PGDATABASE" -U "$PGUSERNAME" -p "$PGPORT"
        shp2pgsql -s 4326 -I shapefiles/intersections/intersections.shp | psql -h "$PGHOST" -d "$PGDATABASE" -U "$PGUSERNAME" -p "$PGPORT"
        shp2pgsql -s 4326 -I shapefiles/statistical_neighborhoods/statistical_neighborhoods.shp | psql -h "$PGHOST" -d "$PGDATABASE" -U "$PGUSERNAME" -p "$PGPORT"