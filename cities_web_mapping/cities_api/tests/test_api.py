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