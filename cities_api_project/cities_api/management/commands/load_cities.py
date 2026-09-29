from django.core.management.base import BaseCommand
from django.contrib.gis.geos import Point
from cities_api.models import City
from data.cities_data import CITIES_DATA

class Command(BaseCommand):
    help = 'Load cities data into the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing cities before loading',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing cities...')
            City.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('✓ Existing cities cleared'))

        self.stdout.write('Loading cities data...')

        created_count = 0
        updated_count = 0

        for city_data in CITIES_DATA:
            # Create Point geometry
            point = Point(city_data['longitude'], city_data['latitude'], srid=4326)

            # Get or create city
            city, created = City.objects.update_or_create(
                name=city_data['name'],
                country=city_data['country'],
                defaults={
                    'region': city_data.get('region', ''),
                    'population': city_data['population'],
                    'location': point,
                    'founded_year': city_data.get('founded_year'),
                    'is_capital': city_data.get('is_capital', False),
                    'timezone': city_data.get('timezone', ''),
                    'elevation_m': city_data.get('elevation_m'),
                }
            )

            if created:
                created_count += 1
                self.stdout.write(f'  ✓ Created: {city}')
            else:
                updated_count += 1
                self.stdout.write(f'  ↻ Updated: {city}')

        self.stdout.write(
            self.style.SUCCESS(
                f'\nData loading complete!\n'
                f'Created: {created_count} cities\n'
                f'Updated: {updated_count} cities\n'
                f'Total: {City.objects.count()} cities in database'
            )
        )