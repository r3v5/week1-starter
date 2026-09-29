# Dublin Spatial Analysis

## Running it

```bash
docker compose up --build -d
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
```

App: http://localhost:8000/
Admin: http://localhost:8000/admin/

## Proof it works

### Running containers

`docker compose ps` — all 3 services up, `db` healthy.

![Running containers](running-containers.png)

### Dashboard

Aggregate stats (admin areas, roads, POIs, zones), top attractions, and the admin areas table, all pulled live from PostGIS via GeoDjango models.

![Dashboard](dashboard.png)

### POI detail — spatial query in action

Detail page for a single POI. "Nearby Roads" is computed with a live PostGIS distance query (`ST_DistanceSphere` via GeoDjango's `distance_lte` + `Distance` annotation) against `DublinRoad` geometries, and the raw GeoJSON geometry of the POI is rendered directly from the database.

![Guinness Storehouse detail](guinness_storehouse.png)

Same page for a POI with a road within range — nearby road, distance, and geometry all populate correctly.

![Phoenix Park Visitor Centre detail](phoenix_park.png)

### Django admin

![Admin login](django-admin.png)

### Spatial SQL queries (pgAdmin)

PostGIS active and reachable from pgAdmin.

![PostGIS version check](post-gis.png)

Query 1: List All POIs Within Dublin City Centre

![Query 1 results](query-1.png)

Query 2: Calculate Road Length Inside Each Zone

![Query 2 results](query-2.png)

Query 3: Find POIs Near Main Roads (Buffer Analysis)

![Query 3 results](query-3.png)

Query 4: Area Coverage Analysis

![Query 4 results](query-4.png)
