# cities/management/commands/populate_all_data.py
# management/commands/populate_all_data.py (create in app or in main project)
from django.core.management.base import BaseCommand
from django.core.management import call_command

class Command(BaseCommand):
    help = 'Populate all European mapping data (cities and regions)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear all existing data before populating',
        )
        parser.add_argument(
            '--cities',
            type=int,
            default=100,
            help='Number of cities to create (default: 100)',
        )
        parser.add_argument(
            '--regions',
            type=int,
            default=50,
            help='Number of regions to create (default: 50)',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🚀 Starting European mapping data population...\n')
        )

        # Populate regions first (as cities might reference them)
        self.stdout.write('📍 Populating regions...')
        call_command(
            'populate_regions',
            clear=options['clear'],
            count=options['regions'],
            verbosity=1
        )

        # Then populate cities
        self.stdout.write('\n🏙️  Populating cities...')
        call_command(
            'populate_cities',
            clear=options['clear'],
            count=options['cities'],
            verbosity=1
        )

        self.stdout.write(
            self.style.SUCCESS(
                f'\n🎉 Data population complete!'
                f'\n   Cities: {options["cities"]}'
                f'\n   Regions: {options["regions"]}'
                f'\n\n💡 You can now:'
                f'\n   - Visit the dashboard at http://localhost:8000/'
                f'\n   - Test API endpoints at http://localhost:8000/api/'
                f'\n   - View admin interface at http://localhost:8000/admin/'
            )
        )