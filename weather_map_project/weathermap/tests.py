from unittest.mock import MagicMock, patch

import requests
from django.core.cache import cache
from django.test import TestCase, override_settings

from .models import City

# Updated to match XWeather's JSON response structure
SAMPLE_RESPONSE = {
    "response": [{
        "periods": [{
            "tempC": 12.3,
            "feelslikeC": 11.0,
            "humidity": 80,
            "pressureMB": 1012,
            "windSpeedMPS": 4.1,
            "weather": "light rain",
            "icon": "10d.png"
        }]
    }]
}

SAMPLE_FORECAST = {
    "response": [{
        "periods": [
            {"dateTimeISO": f"2026-11-1{day}T07:00:00+01:00", "maxTempC": 10 + day,
             "minTempC": 2 + day, "pop": 20, "weather": "Cloudy", "icon": "cloudy.png"}
            for day in range(4)
        ]
    }]
}


def fake_response(payload=None):
    response = MagicMock()
    response.json.return_value = payload
    response.raise_for_status.return_value = None
    return response


@override_settings(XWEATHER_CLIENT_ID="test-client-id", XWEATHER_CLIENT_SECRET="test-client-secret")
class WeatherApiTests(TestCase):
    def setUp(self):
        cache.clear()
        self.city = City.objects.create(
            name="Dublin", country="Ireland", latitude=53.3498, longitude=-6.2603
        )

    def test_cities_json_lists_cities(self):
        response = self.client.get("/api/cities/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()[0]["name"], "Dublin")

    @patch("weathermap.views.requests.get")
    def test_weather_success(self, mock_get):
        mock_get.return_value = fake_response(SAMPLE_RESPONSE)
        response = self.client.get(f"/api/weather/{self.city.id}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["temperature"], 12.3)
        self.assertEqual(response.json()["description"], "light rain")
        self.assertEqual(mock_get.call_args.kwargs["params"]["units"], "metric")

    def test_unknown_city_returns_404(self):
        response = self.client.get("/api/weather/999999/")
        self.assertEqual(response.status_code, 404)

    @override_settings(XWEATHER_CLIENT_ID=None, XWEATHER_CLIENT_SECRET=None)
    def test_missing_key_returns_503(self):
        response = self.client.get(f"/api/weather/{self.city.id}/")
        self.assertEqual(response.status_code, 503)

    @patch("weathermap.views.requests.get")
    def test_rejected_key_does_not_leak_secret(self, mock_get):
        rejected = MagicMock(status_code=401)
        failing = fake_response()
        failing.raise_for_status.side_effect = requests.exceptions.HTTPError(
            "401 Client Error: Unauthorized for url: ...&client_id=test-client-id&client_secret=test-client-secret",
            response=rejected,
        )
        mock_get.return_value = failing

        response = self.client.get(f"/api/weather/{self.city.id}/")
        self.assertEqual(response.status_code, 502)
        self.assertNotIn("test-client-secret", response.content.decode())

    @patch("weathermap.views.requests.get", side_effect=requests.exceptions.Timeout)
    def test_timeout_returns_502(self, mock_get):
        response = self.client.get(f"/api/weather/{self.city.id}/")
        self.assertEqual(response.status_code, 502)

    @patch("weathermap.views.requests.get")
    def test_unexpected_payload_returns_502(self, mock_get):
        mock_get.return_value = fake_response({"unexpected": "shape"})
        response = self.client.get(f"/api/weather/{self.city.id}/")
        self.assertEqual(response.status_code, 502)

    @patch("weathermap.views.requests.get")
    def test_weather_is_cached(self, mock_get):
        mock_get.return_value = fake_response(SAMPLE_RESPONSE)
        first = self.client.get(f"/api/weather/{self.city.id}/")
        second = self.client.get(f"/api/weather/{self.city.id}/")
        self.assertEqual(first.json(), second.json())
        self.assertEqual(mock_get.call_count, 1)

    @patch("weathermap.views.requests.get", side_effect=requests.exceptions.Timeout)
    def test_errors_are_not_cached(self, mock_get):
        self.client.get(f"/api/weather/{self.city.id}/")
        self.client.get(f"/api/weather/{self.city.id}/")
        self.assertEqual(mock_get.call_count, 2)


@override_settings(XWEATHER_CLIENT_ID="test-client-id", XWEATHER_CLIENT_SECRET="test-client-secret")
class ForecastApiTests(TestCase):
    def setUp(self):
        cache.clear()
        self.city = City.objects.create(
            name="Dublin", country="Ireland", latitude=53.3498, longitude=-6.2603
        )

    @patch("weathermap.views.requests.get")
    def test_forecast_returns_three_days(self, mock_get):
        mock_get.return_value = fake_response(SAMPLE_FORECAST)
        response = self.client.get(f"/api/forecast/{self.city.id}/")
        self.assertEqual(response.status_code, 200)
        days = response.json()["forecast"]
        self.assertEqual(len(days), 3)
        self.assertEqual(days[0], {
            "date": "2026-11-10", "max_temp": 10, "min_temp": 2,
            "precipitation_chance": 20, "description": "Cloudy", "icon": "cloudy.png",
        })
        self.assertEqual(mock_get.call_args.kwargs["params"]["filter"], "day")

    def test_forecast_unknown_city_returns_404(self):
        response = self.client.get("/api/forecast/999999/")
        self.assertEqual(response.status_code, 404)

    @patch("weathermap.views.requests.get")
    def test_forecast_rejected_key_does_not_leak_secret(self, mock_get):
        failing = fake_response()
        failing.raise_for_status.side_effect = requests.exceptions.HTTPError(
            "401 Client Error: ...&client_secret=test-client-secret",
            response=MagicMock(status_code=401),
        )
        mock_get.return_value = failing
        response = self.client.get(f"/api/forecast/{self.city.id}/")
        self.assertEqual(response.status_code, 502)
        self.assertNotIn("test-client-secret", response.content.decode())

    @patch("weathermap.views.requests.get")
    def test_forecast_unexpected_payload_returns_502(self, mock_get):
        mock_get.return_value = fake_response({"response": [{"periods": [{"no": "date"}]}]})
        response = self.client.get(f"/api/forecast/{self.city.id}/")
        self.assertEqual(response.status_code, 502)
