# regions/management/commands/populate_regions.py
from django.core.management.base import BaseCommand
from django.contrib.gis.geos import Polygon, MultiPolygon, Point
from regions.models import Region
import random
import math

class Command(BaseCommand):
    help = 'Populate the database with European regions data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing regions before populating',
        )
        parser.add_argument(
            '--count',
            type=int,
            default=50,
            help='Number of regions to create (default: 50)',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing regions...')
            Region.objects.all().delete()

        count = options['count']

        # European regions data with realistic information
        european_regions_data = [
            # Countries (admin_level 1)
            ("Germany", "Germany", "DE", "country", 357022, 83240000, 233, 45000000, 42000, 6.2, 1),
            ("France", "France", "FR", "country", 643801, 67750000, 105, 42000000, 38000, 7.8, 1),
            ("Italy", "Italy", "IT", "country", 301230, 59550000, 198, 36000000, 35000, 9.2, 1),
            ("Spain", "Spain", "ES", "country", 505370, 47350000, 94, 31000000, 32000, 13.1, 1),
            ("Poland", "Poland", "PL", "country", 312679, 38000000, 121, 23000000, 22000, 5.1, 1),
            ("United Kingdom", "United Kingdom", "UK", "country", 243610, 67330000, 276, 45000000, 46000, 4.3, 1),
            ("Netherlands", "Netherlands", "NL", "country", 41543, 17440000, 420, 11500000, 58000, 3.2, 1),
            ("Belgium", "Belgium", "BE", "country", 30528, 11590000, 380, 8200000, 48000, 7.1, 1),
            ("Czech Republic", "Czech Republic", "CZ", "country", 78867, 10700000, 136, 7800000, 28000, 2.1, 1),
            ("Hungary", "Hungary", "HU", "country", 93028, 9750000, 105, 7100000, 22000, 3.4, 1),
            ("Austria", "Austria", "AT", "country", 83879, 9000000, 107, 5800000, 52000, 4.8, 1),
            ("Sweden", "Sweden", "SE", "country", 450295, 10350000, 23, 8900000, 62000, 4.1, 1),
            ("Denmark", "Denmark", "DK", "country", 43094, 5831000, 135, 4900000, 68000, 2.8, 1),
            ("Finland", "Finland", "FI", "country", 338424, 5540000, 16, 4700000, 51000, 6.8, 1),
            ("Norway", "Norway", "NO", "country", 385207, 5380000, 14, 4300000, 78000, 2.4, 1),
            ("Ireland", "Ireland", "IE", "country", 70273, 5010000, 71, 3200000, 55000, 5.2, 1),
            ("Portugal", "Portugal", "PT", "country", 92090, 10290000, 112, 6700000, 32000, 6.9, 1),
            ("Greece", "Greece", "GR", "country", 131957, 10720000, 81, 7900000, 24000, 16.8, 1),
            ("Switzerland", "Switzerland", "CH", "country", 41291, 8700000, 211, 6200000, 89000, 2.1, 1),

            # Major German States (admin_level 2)
            ("Bavaria", "Germany", "DE-BY", "state", 70552, 13130000, 186, 9500000, 55000, 2.8, 2),
            ("North Rhine-Westphalia", "Germany", "DE-NW", "state", 34110, 17930000, 526, 14200000, 49000, 5.1, 2),
            ("Baden-Württemberg", "Germany", "DE-BW", "state", 35751, 11100000, 311, 8900000, 58000, 3.2, 2),
            ("Lower Saxony", "Germany", "DE-NI", "state", 47609, 8000000, 168, 5400000, 45000, 4.7, 2),
            ("Hesse", "Germany", "DE-HE", "state", 21115, 6290000, 298, 4900000, 51000, 4.2, 2),
            ("Saxony", "Germany", "DE-SN", "state", 18416, 4080000, 221, 2600000, 38000, 7.3, 2),

            # French Regions (admin_level 2)
            ("Île-de-France", "France", "FR-IDF", "state", 12012, 12280000, 1022, 11500000, 62000, 5.8, 2),
            ("Auvergne-Rhône-Alpes", "France", "FR-ARA", "state", 69711, 8040000, 115, 5200000, 41000, 6.7, 2),
            ("Nouvelle-Aquitaine", "France", "FR-NAQ", "state", 84036, 6010000, 72, 3400000, 36000, 7.8, 2),
            ("Occitanie", "France", "FR-OCC", "state", 72724, 5880000, 81, 3600000, 34000, 8.9, 2),
            ("Hauts-de-France", "France", "FR-HDF", "state", 31813, 6010000, 189, 4500000, 32000, 11.4, 2),
            ("Grand Est", "France", "FR-GES", "state", 57433, 5560000, 97, 3400000, 35000, 8.2, 2),

            # Italian Regions (admin_level 2)
            ("Lombardy", "Italy", "IT-25", "state", 23844, 10080000, 423, 8200000, 44000, 5.9, 2),
            ("Lazio", "Italy", "IT-62", "state", 17236, 5880000, 341, 5200000, 39000, 7.5, 2),
            ("Campania", "Italy", "IT-72", "state", 13590, 5800000, 427, 4100000, 29000, 15.4, 2),
            ("Veneto", "Italy", "IT-34", "state", 18399, 4910000, 267, 3900000, 38000, 4.8, 2),
            ("Sicily", "Italy", "IT-82", "state", 25711, 4970000, 193, 3100000, 24000, 18.3, 2),
            ("Piedmont", "Italy", "IT-21", "state", 25402, 4360000, 172, 3200000, 38000, 8.7, 2),

            # Spanish Regions (admin_level 2)
            ("Andalusia", "Spain", "ES-AN", "state", 87268, 8460000, 97, 5100000, 29000, 13.1, 2),
            ("Catalonia", "Spain", "ES-CT", "state", 32114, 7750000, 241, 6200000, 35000, 12.8, 2),
            ("Madrid", "Spain", "ES-MD", "state", 8028, 6780000, 845, 6400000, 37500, 8.1, 2),
            ("Valencia", "Spain", "ES-VC", "state", 23255, 5040000, 217, 3800000, 31000, 11.2, 2),
            ("Galicia", "Spain", "ES-GA", "state", 29574, 2700000, 91, 1800000, 28000, 8.9, 2),
            ("Castile and León", "Spain", "ES-CL", "state", 94223, 2400000, 25, 1500000, 30000, 7.4, 2),

            # UK Regions (admin_level 2)
            ("England", "United Kingdom", "GB-ENG", "state", 130279, 56550000, 434, 47000000, 46000, 4.3, 2),
            ("Scotland", "United Kingdom", "GB-SCT", "state", 77933, 5470000, 70, 4200000, 38000, 3.4, 2),
            ("Wales", "United Kingdom", "GB-WLS", "state", 20779, 3140000, 151, 2200000, 31000, 6.8, 2),
            ("Northern Ireland", "United Kingdom", "GB-NIR", "state", 14130, 1890000, 134, 1300000, 33000, 2.8, 2),
        ]

        created_count = 0
        updated_count = 0

        # Create regions from the data
        for name, country, code, region_type, area, population, density, urban_pop, gdp, unemployment, admin_level in european_regions_data:
            if created_count >= count:
                break

            try:
                # Generate a realistic polygon based on the area
                geometry = self._generate_region_polygon(area, country)

                region, created = Region.objects.get_or_create(
                    region_code=code,
                    defaults={
                        'name': name,
                        'country': country,
                        'region_type': region_type,
                        'geometry': geometry,
                        'area_km2': area,
                        'total_population': population,
                        'population_density': density,
                        'urban_population_pct': (urban_pop / population) * 100 if urban_pop and population else None,
                        'gdp_per_capita': gdp,
                        'unemployment_rate': unemployment,
                        'admin_level': admin_level,
                        'agricultural_area_pct': random.uniform(20, 60),
                        'forest_area_pct': random.uniform(15, 45),
                        'urban_area_pct': random.uniform(5, 25),
                        'population_year': random.choice([2022, 2023]),
                        'data_source': 'European Statistical Office'
                    }
                )

                if created:
                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f"✅ Created: {name} ({region_type})")
                    )
                else:
                    updated_count += 1
                    self.stdout.write(
                        self.style.WARNING(f"⚠️  Already exists: {name}")
                    )

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"❌ Error creating {name}: {e}")
                )

        # Generate additional random regions if needed
        if created_count < count:
            additional_needed = count - created_count
            self.stdout.write(f"Generating {additional_needed} additional regions...")

            countries = ["Germany", "France", "Italy", "Spain", "Poland", "United Kingdom", 
                        "Netherlands", "Belgium", "Czech Republic", "Hungary"]
            region_types = ["county", "municipality", "district"]

            for i in range(additional_needed):
                country = random.choice(countries)
                region_name = f"Region_{random.randint(1000, 9999)}"
                region_code = f"{country[:2].upper()}-{random.randint(100, 999)}"

                area = random.uniform(500, 15000)
                population = random.randint(100000, 2000000)

                try:
                    geometry = self._generate_region_polygon(area, country)

                    region = Region.objects.create(
                        name=region_name,
                        country=country,
                        region_code=region_code,
                        region_type=random.choice(region_types),
                        geometry=geometry,
                        area_km2=area,
                        total_population=population,
                        population_density=population / area,
                        urban_population_pct=random.uniform(30, 80),
                        gdp_per_capita=random.randint(20000, 60000),
                        unemployment_rate=random.uniform(2.0, 15.0),
                        admin_level=random.choice([3, 4, 5]),
                        agricultural_area_pct=random.uniform(20, 60),
                        forest_area_pct=random.uniform(15, 45),
                        urban_area_pct=random.uniform(5, 25),
                        population_year=random.choice([2022, 2023]),
                        data_source='Generated Data'
                    )

                    created_count += 1
                    if created_count % 10 == 0:
                        self.stdout.write(f"Generated {created_count}/{count} regions...")

                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"❌ Error generating region {region_name}: {e}")
                    )

        self.stdout.write(
            self.style.SUCCESS(
                f'\n🎉 Region population complete!'
                f'\nCreated: {created_count}'
                f'\nExisting: {updated_count}'
                f'\nTotal regions in database: {Region.objects.count()}'
            )
        )

    def _generate_region_polygon(self, area_km2, country):
        """Generate a realistic polygon for a region based on its area and country"""

        # Country center coordinates (approximate)
        country_centers = {
            "Germany": (51.1657, 10.4515),
            "France": (46.6034, 1.8883),
            "Italy": (41.8719, 12.5674),
            "Spain": (40.4637, -3.7492),
            "Poland": (51.9194, 19.1451),
            "United Kingdom": (55.3781, -3.4360),
            "Netherlands": (52.1326, 5.2913),
            "Belgium": (50.5039, 4.4699),
            "Czech Republic": (49.8175, 15.4730),
            "Hungary": (47.1625, 19.5033),
            "Austria": (47.5162, 14.5501),
            "Sweden": (60.1282, 18.6435),
            "Denmark": (56.2639, 9.5018),
            "Finland": (61.9241, 25.7482),
            "Norway": (60.4720, 8.4689),
            "Ireland": (53.1424, -7.6921),
            "Portugal": (39.3999, -8.2245),
            "Greece": (39.0742, 21.8243),
            "Switzerland": (46.8182, 8.2275),
        }

        # Get country center or use default
        center_lat, center_lng = country_centers.get(country, (50.0, 10.0))

        # Add some randomness to the center
        center_lat += random.uniform(-2, 2)
        center_lng += random.uniform(-2, 2)

        # Calculate approximate radius from area (assuming roughly circular region)
        radius_km = math.sqrt(area_km2 / math.pi)

        # Convert radius to degrees (very rough approximation)
        radius_deg = radius_km / 111.0  # 1 degree ≈ 111 km

        # Generate polygon points
        num_points = random.randint(6, 12)  # Variable number of sides
        points = []

        for i in range(num_points):
            angle = (2 * math.pi * i) / num_points
            # Add some irregularity
            angle_offset = random.uniform(-0.3, 0.3)
            radius_variation = random.uniform(0.7, 1.3)

            point_radius = radius_deg * radius_variation
            point_lat = center_lat + point_radius * math.cos(angle + angle_offset)
            point_lng = center_lng + point_radius * math.sin(angle + angle_offset)

            points.append((point_lng, point_lat))

        # Close the polygon
        points.append(points[0])

        # Create polygon
        polygon = Polygon(points, srid=4326)

        # Convert to MultiPolygon (required by the model)
        multi_polygon = MultiPolygon([polygon], srid=4326)

        return multi_polygon