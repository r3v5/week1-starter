# Real-Time Weather Map

## Project Overview

An interactive web map which shows the current weather and a 3 day forecast for cities around the world. The cities are stored in a PostGIS database and are displayed as markers on a Leaflet map. Click on a marker (or search for a city) and a popup will appear with the current conditions pulled in from the [XWeather](https://www.xweather.com/) API.

The browser never speaks to XWeather at all. Django is the server side proxy. It makes the call to XWeather using the secret credentials, only returns the fields that the map actually needs, caches the result for 10 minutes and then just returns plain old JSON to the browser.


## Setup Instructions

Requirements: Docker Desktop (with Docker Compose v2) and an XWeather account.

1. Copy the example environment file and fill in every value:

   ```bash
   cp .env.example .env
   ```

   Typical local values: `DATABASE_HOST=db`, `DATABASE_PORT=5432`, `DJANGO_DEBUG=True`. Your XWeather client ID and secret (see [API Keys](#api-keys)).

   If the value contains a $ (which is fairly common in generated Django secret keys) then you need to wrap it in single quotes or write $$ otherwise Docker Compose is going to treat it as a variable and just silently drop part of the value.

2. Build the image:

   ```bash
   docker compose build
   ```

3. Create the database tables and load the starter cities:

   ```bash
   docker compose run --rm web python manage.py migrate
   docker compose run --rm web python manage.py populate_cities
   ```

4. (Optional) Create an admin user to add or edit cities at `/admin/`:

   ```bash
   docker compose run --rm web python manage.py createsuperuser
   ```

5. Start the stack:

   ```bash
   docker compose up -d
   ```

| URL | Service |
| --- | --- |
| http://localhost:8000/ | Weather map |
| http://localhost:8000/admin/ | Django admin (manage cities) |
| http://localhost:5050/ | pgAdmin (register server host `db`, port `5432`) |

Run the tests:

```bash
docker compose run --rm web python manage.py test weathermap
```

The project folder is mounted into the web container so code changes will reload automatically. If something isn't updating then have a look at `docker compose logs --tail=50 web`.

## API Keys

1. Sign up at xweather.com (there's a free developer trial available).
2. In the account dashboard, create an application. Use `localhost` as the namespace for local development.
3. Copy the **Client ID** and **Client Secret** into `.env`:

   ```
   XWEATHER_CLIENT_ID=...
   XWEATHER_CLIENT_SECRET=...
   ```

How the credentials reach Django:

1. .env exists only on your machine and is listed in .gitignore.
2. Docker Compose reads the .env file and passes those values into the web container via the environment: section in compose.yaml.
3. settings.py reads them via os.environ.get(...)
4. Only `weathermap/views.py` makes use of them, in the server side requests to XWeather.

The creds are never in the source code, never in the browser, never in any API response. The error messages are hand written and never contain `str(e)` as the requests exceptions will contain the full request URL (with the creds in it).

## Features

- Interactive Leaflet map with OpenStreetMap tiles and one marker per city
- Current weather popup: temperature, feels like, humidity, wind speed, pressure, description and icon
- **3-day forecast** in a second popup tab (high/low, chance of rain, icon), loaded the first time the tab is opened
- **Caching**: weather and forecast responses are cached for 10 minutes with Django's cache framework; errors are not cached
- **City search**: filter by city or country, pick with mouse or keyboard (arrow keys, Enter, Esc), zoom to the city and open its popup
- **°C / °F toggle** in the header; conversion happens in the browser, so cached metric data serves both units
- City management through the Django admin; new cities appear on the map after a reload
- Clear error popups for missing credentials (503), rejected credentials, timeouts, and unexpected responses (502)
- Text from external APIs is HTML-escaped before it is placed in popups
- Automated tests with mocked XWeather calls (no network or real key needed)

### API endpoints

| Endpoint | Returns |
| --- | --- |
| `GET /api/cities/` | All cities: id, name, country, latitude, longitude |
| `GET /api/weather/<city_id>/` | Current conditions (metric) |
| `GET /api/forecast/<city_id>/` | 3 daily forecast entries (metric) |

## Technologies Used

**Docker services** (`compose.yaml`)

- `db`: PostgreSQL 16 with PostGIS 3.4 (`postgis/postgis:16-3.4`)
- `web`: Python 3.12 image running Django's development server
- `pgadmin`: pgAdmin 4 for inspecting the database

**Backend**

- Django 5 (with `django.contrib.gis`), psycopg 3
- `requests` for calls to XWeather
- Django cache framework (`LocMemCache`)
- Django test framework with `unittest.mock`

**Frontend**

- Leaflet 1.9.4 with OpenStreetMap tiles
- Vanilla JavaScript (Fetch API, async/await) and CSS

**External API**

- XWeather `conditions/closest` (current weather) and `forecasts/closest` (daily forecast)

## Challenges Faced

- Unstyled page stuck on "Loading weather data..." - the template did load css/styles.css, it just had the wrong name (it was called style.css) so the server returned a 404. Without the CSS the map had no height and the loading overlay was therefore always present. Renaming the file sorted both of those issues.
- The secret key was cut short by Docker Compose (it had a $neay in it which Compose interpreted as a variable and substituted with an empty string - 'The "neay" variable is not set` warning). Fix: either put the value in single quotes or escape it as $$ .
- Forecast tab closed the popup: redrawing the entire popup resulted in the tab button being removed whilst the click was still in progress. Leaflet then interpreted that as a click on the map and closed the popup. The tab buttons are now created once and only the panel content is replaced.
- Different API to the handout: XWeather has the data nested under response[0].periods and can return one entry per day (via filter=day) so no need to filter out the 3-hour entries at all.
- Slow or failed upstream calls: one XWeather call did hit the 5 second timeout. The view returns a 502 with a very clear error message and that error is not cached so the next click will try again.

## Future Improvements

- Shared Redis cache service so cached data survives restarts and is shared between `web` containers
- Production setup: Gunicorn, `DEBUG=False`, WhiteNoise or a reverse proxy for static files, and no source code mount
- Marker clustering for large numbers of cities
- Visual alerts for extreme temperatures (below 0°C or above 35°C)
- Store weather history in the database and show temperature trends
- Use a PostGIS `PointField` for city locations to allow spatial queries (for example "cities within 100 km")
- User accounts with saved favourite cities