import requests
from django.conf import settings
from django.core.cache import cache
from django.http import JsonResponse
from django.shortcuts import render

from .models import City

XWEATHER_CONDITIONS_URL = "https://data.api.xweather.com/conditions/closest"
XWEATHER_FORECAST_URL = "https://data.api.xweather.com/forecasts/closest"

# Weather data is cached for 10 minutes to reduce calls to XWeather
CACHE_TIMEOUT = 600
FORECAST_DAYS = 3


class XWeatherError(Exception):
    """An error that is safe to show to the browser (never contains credentials)."""

    def __init__(self, message, status):
        super().__init__(message)
        self.message = message
        self.status = status


def map_view(request):
    """Render the main map page"""
    return render(request, 'weathermap/map.html')


def get_cities_json(request):
    """Return all cities as JSON"""
    cities = City.objects.all().values('id', 'name', 'country', 'latitude', 'longitude')
    return JsonResponse(list(cities), safe=False)


def fetch_xweather_periods(url, city, extra_params=None):
    """
    Call an XWeather endpoint for a city (server-side, so credentials stay secret)
    and return its list of periods. Raises XWeatherError with a safe message.
    """
    client_id = getattr(settings, 'XWEATHER_CLIENT_ID', None)
    client_secret = getattr(settings, 'XWEATHER_CLIENT_SECRET', None)
    if not client_id or not client_secret:
        raise XWeatherError(
            'XWeather API credentials (XWEATHER_CLIENT_ID and XWEATHER_CLIENT_SECRET) are not configured',
            503,
        )

    params = {
        'p': f"{city.latitude},{city.longitude}",
        'client_id': client_id,
        'client_secret': client_secret,
        **(extra_params or {}),
    }

    try:
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        # XWeather returns data nested inside response -> periods
        return response.json()['response'][0]['periods']
    except requests.exceptions.HTTPError as e:
        # Never return str(e): it contains the request URL, including sensitive credentials
        status = e.response.status_code
        if status == 401:
            raise XWeatherError('XWeather rejected the API credentials', 502)
        raise XWeatherError(f'XWeather returned HTTP {status}', 502)
    except requests.exceptions.RequestException:
        raise XWeatherError('Could not get a response from XWeather', 502)
    except (KeyError, IndexError, TypeError, ValueError):
        raise XWeatherError('Unexpected response format from XWeather', 502)


def cached_city_weather(request, city_id, kind, build_result):
    """
    Shared flow for weather endpoints: look up the city, serve from cache when
    possible, otherwise build the result and cache it (successful results only).
    """
    cache_key = f'{kind}_{city_id}'
    cached_data = cache.get(cache_key)
    if cached_data:
        return JsonResponse(cached_data)

    try:
        city = City.objects.get(id=city_id)
    except City.DoesNotExist:
        return JsonResponse({'error': 'City not found'}, status=404)

    try:
        result = build_result(city)
    except XWeatherError as e:
        return JsonResponse({'error': e.message}, status=e.status)

    cache.set(cache_key, result, CACHE_TIMEOUT)
    return JsonResponse(result)


def get_weather(request, city_id):
    """Current weather for a city (metric units; the browser converts to °F if asked)"""

    def build(city):
        periods = fetch_xweather_periods(XWEATHER_CONDITIONS_URL, city, {'units': 'metric'})
        try:
            period = periods[0]
        except IndexError:
            raise XWeatherError('Unexpected response format from XWeather', 502)
        return {
            'city': city.name,
            'country': city.country,
            'temperature': period.get('tempC'),
            'feels_like': period.get('feelslikeC'),
            'humidity': period.get('humidity'),
            'pressure': period.get('pressureMB'),
            'wind_speed': period.get('windSpeedMPS'),
            'description': period.get('weather'),
            'icon': period.get('icon'),
        }

    return cached_city_weather(request, city_id, 'weather', build)


def get_forecast(request, city_id):
    """3-day forecast for a city: one daily period per day from XWeather"""

    def build(city):
        periods = fetch_xweather_periods(
            XWEATHER_FORECAST_URL, city, {'filter': 'day', 'limit': FORECAST_DAYS}
        )
        try:
            days = [{
                'date': period['dateTimeISO'][:10],  # e.g. 2026-11-10
                'max_temp': period.get('maxTempC'),
                'min_temp': period.get('minTempC'),
                'precipitation_chance': period.get('pop'),
                'description': period.get('weather'),
                'icon': period.get('icon'),
            } for period in periods[:FORECAST_DAYS]]
        except (KeyError, TypeError):
            raise XWeatherError('Unexpected response format from XWeather', 502)
        if not days:
            raise XWeatherError('Unexpected response format from XWeather', 502)
        return {'city': city.name, 'country': city.country, 'forecast': days}

    return cached_city_weather(request, city_id, 'forecast', build)
