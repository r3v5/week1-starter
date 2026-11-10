# Lab 7 Reflection: Real-Time Weather Mapping

## 1. Architecture

The data flow from clicking a marker to seeing the weather:

1. Page load (browser to Django): browser requests `/` and Django serves up map.html which loads Leaflet, styles.css and map.js.
2. City list (Django to database): map.js makes a call to GET /api/cities/. The get_cities_json view queries the weathermap_city table in the db container (PostGIS) via the internal Docker network (host db on port 5432) and returns the list of cities as JSON. map.js then draws one marker for each city.
3. Marker click (browser to Django): clicking a marker triggers a call to `GET /api/weather/<city_id>/` on our own server. The browser doesn't make any contact with XWeather.
4. Cache check (Django): get_weather looks up the key `weather_<city_id>` in Django's cache. On a hit it just returns the JSON that's in the cache and steps 5 and 6 are skipped.
5. City lookup (Django to database): on a cache miss Django will pull the city's lat/long from the database. An unknown id will return 404.
6. Upstream call (Django to XWeather): Django makes a server-side HTTPS call to XWeather's conditions/closest endpoint with the lat/lng and the client ID and secret from the container environment. It keeps only the fields the map requires, caches them for 10 minutes and returns them as JSON.
7. **Display (browser)**: map.js escapes the text, converts the temp to °F if the toggle is on and then displays the popup on the marker. If you open the Forecast tab it will repeat steps 3 to 7 with /api/forecast/<city_id>/

```
Browser ──/api/weather/5/──▶ Django (web container) ──cache hit?──▶ return JSON
                                  │ miss
                                  ├──▶ PostGIS (db container): city coordinates
                                  └──▶ XWeather API (HTTPS, with credentials)
                                  ◀── trimmed JSON, cached 10 min
Browser ◀── JSON ── Django
```

## 2. Security

**Measures in place**

- The XWeather credentials are used solely on the server. Django acts as a proxy so the credentials never make it to the browser.
- The credentials are in the .env file (which is git ignored) and .env.example just contains the variable names.
- The error responses use fixed messages and never use `str(e)` as the requests exception message would contain the full URL including the client_secret. A test checks that the secret isn't in the response.
- The weather text from XWeather is HTML escaped (via escapeHtml) before it gets into the popup HTML, which prevents XSS from the upstream data. The icon name is URL encoded.
- ALLOWED_HOSTS is restricted to localhost and 127.0.0.1.
- The database is not published to the host. Only web and pgadmin have ports exposed.
- Upstream requests have a 5 second timeout so a slow API won't be able to hold a worker for ever.
- City data can only be altered via the Django admin (which of course requires a staff login).

**Additional measures that could be added**

- Rate limiting on /api/weather/ and /api/forecast/ (e.g. using django-ratelimit) so no-one can blow through the XWeather quota.
- Production settings: DEBUG=False, a robust SECRET_KEY (no default), HTTPS, SECURE_SSL_REDIRECT, secure cookies and HSTS.
- A Content Security Policy which will only allow scripts from our server and unpkg.com.
- Subresource Integrity (integrity= attributes) on the Leaflet files loaded from the CDN.
- Docker secrets or a secrets manager rather than plain environment variables in production.
- Not publishing pgAdmin outside of development.

**Where the API key exists, and where it must never appear**

| Location | Key present? |
| --- | --- |
| `.env` on the host | Yes, the single source |
| `web` container environment (via `compose.yaml`) | Yes |
| Django `settings` at runtime (`os.environ`) | Yes |
| Outbound request from Django to XWeather | Yes, over HTTPS |
| Source code, `compose.yaml`, `.env.example`, git history | **Never** |
| Browser, JavaScript, HTML, API responses, error messages | **Never** |
| Logs and screenshots | **Never** |

## 3. Performance

**Potential bottlenecks**

- XWeather latency: each cache miss will wait 1-5 seconds for the upstream API and the dev server ties up a thread for the whole wait.
- API quota: every miss uses up a call from the XWeather plan.
- One marker per city: thousands of DOM markers will make Leaflet very slow to pan and zoom.
- Unpaginated city list: /api/cities/ returns all the rows in a single response.
- Per-process cache: LocMemCache is lost on every reload and isn't shared between processes so we end up with very low cache hit rates with multiple workers.
- Development server: runserver is not built for concurrent traffic.

**Optimizing for 1000+ cities**

- Use Leaflet.markercluster to cluster the markers, or draw them on a canvas layer (preferCanvas) rather than as DOM elements.
- Just load the cities that are within the visible map area. Send the map bounds with the request, filter in the database using a PostGIS PointField and a spatial index (location__within=bbox) and reload when the map moves.
- Move the cache to Redis so all the workers can share it and it survives restarts.
- Pre-fetch the weather for the most popular cities via a background job (Celery or cron) so that users are extremely unlikely to be waiting for a miss.
- Use XWeather batch requests to get multiple locations in a single call.
- Run Gunicorn with multiple workers or use async views with httpx so that slow upstream calls don't block other users.
- Serve the static files and the city list either with long-lived cache headers or via a CDN.

## 4. Error Handling

| Where | Possible error | Current handling |
| --- | --- | --- |
| Leaflet CDN | Script fails to load | `map.js` checks `typeof L` and shows an alert |
| `/api/cities/` | Network or server error | Error popup in the centre of the map |
| `/api/cities/` | No cities in the database | Popup telling the user to run `populate_cities` |
| Weather or forecast view | Unknown city id | 404 `City not found` |
| Weather or forecast view | Credentials not configured | 503 with a clear message |
| XWeather | Credentials rejected (401) | 502 `XWeather rejected the API credentials` |
| XWeather | Other HTTP error (429, 500, ...) | 502 `XWeather returned HTTP <status>` |
| XWeather | Timeout or connection failure | 502 `Could not get a response from XWeather` |
| XWeather | Unexpected JSON shape or empty result | 502 `Unexpected response format` |
| Browser | Non-JSON error body | `.catch(() => ({}))` falls back to an HTTP status message |
| Browser | Any weather or forecast error | Error popup or an error message in the Forecast tab |
| Database | `db` unavailable | Django returns a 500 page (not handled specifically) |

**Are they handled appropriately?** Mostly. All upstream failures give a clear error message, never leak the credentials and are not cached so a retry can succeed. The tests cover 404s, 503s, 401s, timeouts and bad payloads for both the weather and forecast views.

**Improvements**

- Return a message for 429 (quota exceeded) and add a retry with back-off for the short failures.
- If XWeather is down then serve slightly stale cached data rather than an error.
- Return a JSON 503 when the DB is unreachable and include a /health/ endpoint for Docker health checks.
- Log upstream failures on the server (without the URL or credentials) so that we can monitor the problems.
- Add a "Retry" button to the error popup.
- Abort browser requests that take too long (via AbortController) and drop late responses if the user has already clicked on a different city.

## 5. Scalability: user accounts, favourites and history

- User accounts: use Django's built-in django.contrib.auth (login, logout, registration views). Protect your personal endpoints with @login_required or move over to Django REST Framework (it's already in requirements.txt) with either session or token auth.
- **Favourite cities**: add a many-to-many relation:

  ```python
  class Favorite(models.Model):
      user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
      city = models.ForeignKey(City, on_delete=models.CASCADE)
      created_at = models.DateTimeField(auto_now_add=True)

      class Meta:
          constraints = [models.UniqueConstraint(fields=["user", "city"], name="unique_favorite")]
  ```

  Add GET/POST/DELETE /api/favorites/ endpoints. Show the favourites with a star marker icon and a sidebar list.
- Historical weather: add a WeatherObservation model (city, observed_at, temperature, humidity, wind_speed, pressure, description) with an index on (city, observed_at). A scheduled job (Celery beat or cron) will record the observations hourly which means we won't be making calls to XWeather on every page view. Add /api/history/<city_id>/?from=&to= and plot the trend in the popup with Chart.js. For large volumes we'll need TimescaleDB or monthly table partitioning and will either delete or summarise the old rows.
- **Infrastructure**: add Redis for caching and as the Celery broker, run several Gunicorn workers behind Nginx, and change the city model to a PostGIS `PointField` for spatial queries.

## 6. Deployment

The current stack is development oriented: runserver, source folder mounted into the container, DEBUG on and a cache in memory. For production I would change:

**Dockerfile**

- Use a multi-stage build: build in a builder stage and then just copy over the installed packages and the app into a slim runtime image. Use the runtime `libgdal` libraries rather than the `-dev` packages.
- Split requirements.txt: production dependencies only (add gunicorn, whitenoise, django-redis), with tests and dev tools in requirements-dev.txt.
- Run `python manage.py collectstatic --noinput` as part of the build and serve the static files via WhiteNoise or Nginx.
- Run as a non-root user (USER app)
- Start with Gunicorn: CMD ["gunicorn", "weathermap_config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
- Add a HEALTHCHECK on a /health/ endpoint.

**compose.yaml**

- Remove the .:/app bind mount as the code is already in the image.
- Remove the `command: runserver` override.
- Set DEBUG=False, a good strong SECRET_KEY and ALLOWED_HOSTS read from the environment.
- Pass the secrets via Docker secrets or the hosting platform's secret store rather than via a .env file on the server.
- Add a redis service and set CACHES to django.core.cache.backends.redis.RedisCache at redis://redis:6379/1 so all the web replicas can share one cache.
- Have Nginx (or a cloud load balancer) in front for HTTPS, compression and static files. Don't publish the web, db or pgadmin ports out to the internet and remove pgAdmin from production.
- Add restart: unless-stopped, resource limits and log rotation.
- Run the migrations as a separate one-off step on each release (docker compose run --rm web python manage.py migrate) rather than when the container starts.
- Use a managed PostgreSQL/PostGIS service (or at the very least have scheduled backups of the postgis_data volume).
