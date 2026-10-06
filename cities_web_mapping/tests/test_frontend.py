import requests
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import Client
from django.urls import reverse

class MapViewTests(StaticLiveServerTestCase):
    def setUp(self):
        self.client = Client()

    def test_map_view_loads(self):
        """Test that the map page loads successfully"""
        response = self.client.get('/map/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Leaflet', response.content.decode())

    def test_static_files_served(self):
        """Test that static files are accessible"""
        response = requests.get(f'{self.live_server_url}/static/js/map.js')
        self.assertEqual(response.status_code, 200)

        response = requests.get(f'{self.live_server_url}/static/css/styles.css')
        self.assertEqual(response.status_code, 200)