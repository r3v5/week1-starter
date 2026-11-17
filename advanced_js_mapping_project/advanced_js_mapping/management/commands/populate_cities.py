from django.contrib.gis.geos import Point
from django.core.management.base import BaseCommand
from django.db import transaction

from advanced_js_mapping.models import AdvancedCity

# Population values are approximate examples, not current official statistics.
CITIES = [
    ("London", "United Kingdom", 51.5074, -0.1278, 9000000),
    ("Paris", "France", 48.8566, 2.3522, 2100000),
    ("New York", "United States", 40.7128, -74.0060, 8300000),
    ("Tokyo", "Japan", 35.6762, 139.6503, 14000000),
    ("Sydney", "Australia", -33.8688, 151.2093, 5300000),
    ("Dubai", "UAE", 25.2048, 55.2708, 3600000),
    ("São Paulo", "Brazil", -23.5505, -46.6333, 11400000),
    ("Mumbai", "India", 19.0760, 72.8777, 12400000),
    ("Cairo", "Egypt", 30.0444, 31.2357, 10000000),
    ("Moscow", "Russia", 55.7558, 37.6173, 13000000),
    ("Dublin", "Ireland", 53.3498, -6.2603, 592000),
    ("Cork", "Ireland", 51.8985, -8.4756, 224000),
    ("Belfast", "United Kingdom", 54.5973, -5.9301, 345000),
    ("Edinburgh", "United Kingdom", 55.9533, -3.1883, 527000),
    ("Berlin", "Germany", 52.5200, 13.4050, 3850000),
    ("Munich", "Germany", 48.1351, 11.5820, 1580000),
    ("Amsterdam", "Netherlands", 52.3676, 4.9041, 920000),
    ("Brussels", "Belgium", 50.8503, 4.3517, 195000),
    ("Madrid", "Spain", 40.4168, -3.7038, 3400000),
    ("Barcelona", "Spain", 41.3874, 2.1686, 1700000),
    ("Lisbon", "Portugal", 38.7223, -9.1393, 550000),
    ("Rome", "Italy", 41.9028, 12.4964, 2750000),
    ("Milan", "Italy", 45.4642, 9.1900, 1370000),
    ("Vienna", "Austria", 48.2082, 16.3738, 2000000),
    ("Prague", "Czechia", 50.0755, 14.4378, 1380000),
    ("Warsaw", "Poland", 52.2297, 21.0122, 1860000),
    ("Budapest", "Hungary", 47.4979, 19.0402, 1680000),
    ("Copenhagen", "Denmark", 55.6761, 12.5683, 660000),
    ("Stockholm", "Sweden", 59.3293, 18.0686, 990000),
    ("Oslo", "Norway", 59.9139, 10.7522, 720000),
    ("Helsinki", "Finland", 60.1699, 24.9384, 675000),
    ("Athens", "Greece", 37.9838, 23.7275, 640000),
    ("Zurich", "Switzerland", 47.3769, 8.5417, 440000),
]


class Command(BaseCommand):
    help = "Add sample cities for the advanced mapping lab without changing existing cities"

    @transaction.atomic
    def handle(self, *args, **options):
        created_count = 0
        for name, country, latitude, longitude, population in CITIES:
            _, created = AdvancedCity.objects.get_or_create(
                name=name,
                country=country,
                defaults={
                    "location": Point(longitude, latitude, srid=4326),
                    "population": population,
                },
            )
            created_count += created

        self.stdout.write(self.style.SUCCESS(
            f"{created_count} created, {len(CITIES) - created_count} already present; "
            f"{AdvancedCity.objects.count()} cities in the database"
        ))
