from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.gis.geos import Point
from cities_api.models import City

class CityAPITestCase(APITestCase):
    """Test cases for Cities API"""

    def setUp(self):
        """Create test data"""
        self.dublin = City.objects.create(
            name='Dublin',
            country='Ireland',
            population=1400000,
            location=Point(-6.2603, 53.3498, srid=4326),
            is_capital=True
        )

        self.london = City.objects.create(
            name='London',
            country='United Kingdom',
            population=9000000,
            location=Point(-0.1278, 51.5074, srid=4326),
            is_capital=True
        )

    def test_city_list(self):
        """Test city list endpoint"""
        url = reverse('cities_api:city-list-create')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        self.assertIn('results', response.data)

    def test_city_detail(self):
        """Test city detail endpoint"""
        url = reverse('cities_api:city-detail', kwargs={'pk': self.dublin.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Dublin')
        self.assertEqual(response.data['country'], 'Ireland')

    def test_city_creation(self):
        """Test creating a new city"""
        url = reverse('cities_api:city-list-create')
        data = {
            'name': 'Paris',
            'country': 'France',
            'population': 11000000,
            'latitude': 48.8566,
            'longitude': 2.3522,
            'is_capital': True
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(City.objects.count(), 3)

    def test_city_filtering(self):
        """Test city filtering"""
        url = reverse('cities_api:city-list-create')
        response = self.client.get(url, {'country': 'Ireland'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['name'], 'Dublin')

    def test_geojson_format(self):
        """Test GeoJSON output"""
        url = reverse('cities_api:city-geojson')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['type'], 'FeatureCollection')
        self.assertIn('features', response.data)

    def test_within_radius_query(self):
        """Test spatial within radius query"""
        url = reverse('cities_api:cities-within-radius')
        data = {
            'latitude': 53.0,
            'longitude': -6.0,
            'radius_km': 100
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('cities', response.data)
        self.assertGreater(response.data['count'], 0)

    def test_statistics_endpoint(self):
        """Test statistics endpoint"""
        url = reverse('cities_api:city-statistics')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_cities'], 2)
        self.assertEqual(response.data['capitals_count'], 2)

class ProximitySearchAPITestCase(APITestCase):
    """Tests for the Lab 5 nearest-city and radius endpoints"""

    def setUp(self):
        self.nearest_url = reverse('cities_api:find_nearest_cities')
        self.radius_url = reverse('cities_api:cities_within_radius')
        self.dublin_point = {'lat': 53.3498, 'lng': -6.2603}
        cities = [
            ('Dublin', 'Ireland', -6.2603, 53.3498),
            ('London', 'United Kingdom', -0.1278, 51.5074),
            ('Paris', 'France', 2.3522, 48.8566),
            ('New York', 'United States', -74.0060, 40.7128),
        ]
        for name, country, lng, lat in cities:
            City.objects.create(
                name=name,
                country=country,
                population=1000000,
                location=Point(lng, lat, srid=4326),
            )

    def test_nearest_cities_ordered_by_distance(self):
        response = self.client.post(self.nearest_url, self.dublin_point, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_found'], 4)
        results = response.data['nearest_cities']
        self.assertEqual(
            [city['name'] for city in results],
            ['Dublin', 'London', 'Paris', 'New York'],
        )
        self.assertEqual([city['rank'] for city in results], [1, 2, 3, 4])
        self.assertEqual(results[0]['distance_km'], 0)
        self.assertAlmostEqual(results[1]['distance_km'], 463, delta=5)

    def test_nearest_cities_limited_to_ten(self):
        for i in range(12):
            City.objects.create(
                name=f'Extra {i}',
                country='Testland',
                population=1000,
                location=Point(i, 0, srid=4326),
            )
        response = self.client.post(self.nearest_url, self.dublin_point, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_found'], 10)
        self.assertEqual(len(response.data['nearest_cities']), 10)

    def test_radius_returns_only_cities_inside_radius(self):
        data = {**self.dublin_point, 'radius_km': 500}
        response = self.client.post(self.radius_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['radius_km'], 500)
        self.assertEqual(
            [city['name'] for city in response.data['cities']],
            ['Dublin', 'London'],
        )
        for city in response.data['cities']:
            self.assertLessEqual(city['distance_km'], 500)

    def test_radius_defaults_to_100_km(self):
        response = self.client.post(self.radius_url, self.dublin_point, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['radius_km'], 100)
        self.assertEqual(response.data['total_found'], 1)

    def test_invalid_coordinate_ranges_rejected(self):
        for url in (self.nearest_url, self.radius_url):
            for point in ({'lat': 91, 'lng': 0}, {'lat': -91, 'lng': 0},
                          {'lat': 0, 'lng': 181}, {'lat': 0, 'lng': -181}):
                with self.subTest(url=url, point=point):
                    response = self.client.post(url, point, format='json')
                    self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                    self.assertIn('error', response.data)

    def test_missing_or_non_numeric_input_rejected(self):
        for url in (self.nearest_url, self.radius_url):
            for data in ({}, {'lat': 53.3}, {'lng': -6.2},
                         {'lat': 'north', 'lng': -6.2}, {'lat': None, 'lng': -6.2}):
                with self.subTest(url=url, data=data):
                    response = self.client.post(url, data, format='json')
                    self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                    self.assertIn('error', response.data)

    def test_invalid_radius_rejected(self):
        for radius in (0, -5, 20001, 'far', None):
            with self.subTest(radius=radius):
                data = {**self.dublin_point, 'radius_km': radius}
                response = self.client.post(self.radius_url, data, format='json')
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn('error', response.data)

    def test_get_not_allowed(self):
        response = self.client.get(self.nearest_url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
