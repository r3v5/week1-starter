# cities/management/commands/populate_cities.py
from itertools import count
from django.core.management.base import BaseCommand
from django.contrib.gis.geos import Point
from cities.models import City
import random

class Command(BaseCommand):
    help = 'Populate the database with European cities data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing cities before populating',
        )
        parser.add_argument(
            '--count',
            type=int,
            default=100,
            help='Number of cities to create (default: 100)',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing cities...')
            City.objects.all().delete()

        count = options['count']

        # European cities data with realistic coordinates and information
        european_cities_data = [
            # Major European Cities with real data
            ("London", "United Kingdom", 8982000, 51.5074, -0.1278, "capital", 1572, 33.0, 65000, 4.5, 15.2),
            ("Paris", "France", 2161000, 48.8566, 2.3522, "capital", 105, 20500, 68000, 3.8, 18.5),
            ("Berlin", "Germany", 3669000, 52.5200, 13.4050, "capital", 891, 4119, 42000, 6.2, 29.8),
            ("Madrid", "Spain", 3223000, 40.4168, -3.7038, "capital", 604, 5336, 37500, 8.1, 21.3),
            ("Rome", "Italy", 2873000, 41.9028, 12.4964, "capital", 1285, 2236, 39000, 7.5, 13.2),
            ("Amsterdam", "Netherlands", 873000, 52.3676, 4.9041, "capital", 219, 3987, 58000, 3.2, 25.7),
            ("Vienna", "Austria", 1911000, 48.2082, 16.3738, "capital", 414, 4616, 52000, 4.8, 50.3),
            ("Prague", "Czech Republic", 1309000, 50.0755, 14.4378, "capital", 496, 2640, 28000, 2.1, 31.1),
            ("Budapest", "Hungary", 1752000, 47.4979, 19.0402, "capital", 525, 3337, 22000, 3.4, 28.9),
            ("Warsaw", "Poland", 1790000, 52.2297, 21.0122, "capital", 517, 3464, 18500, 4.7, 25.4),
            ("Stockholm", "Sweden", 975000, 59.3293, 18.0686, "capital", 188, 5187, 62000, 4.1, 44.2),
            ("Copenhagen", "Denmark", 648000, 55.6761, 12.5683, "capital", 88, 7267, 68000, 2.8, 32.1),
            ("Helsinki", "Finland", 658000, 60.1699, 24.9384, "capital", 716, 919, 51000, 6.8, 38.7),
            ("Oslo", "Norway", 697000, 59.9139, 10.7522, "capital", 454, 1537, 78000, 2.4, 42.3),
            ("Dublin", "Ireland", 555000, 53.3498, -6.2603, "capital", 318, 1746, 55000, 5.2, 16.8),
            ("Lisbon", "Portugal", 505000, 38.7223, -9.1393, "capital", 100, 5050, 32000, 6.9, 19.5),
            ("Brussels", "Belgium", 1211000, 50.8503, 4.3517, "capital", 161, 7522, 48000, 7.1, 21.7),
            ("Zurich", "Switzerland", 415000, 47.3769, 8.5417, "major", 88, 4715, 89000, 2.1, 26.4),
            ("Barcelona", "Spain", 1620000, 41.3851, 2.1734, "major", 101, 16040, 35000, 12.8, 18.3),
            ("Milan", "Italy", 1379000, 45.4642, 9.1900, "major", 181, 7616, 44000, 5.9, 12.7),
            ("Munich", "Germany", 1488000, 48.1351, 11.5820, "major", 310, 4800, 55000, 3.2, 31.5),
            ("Hamburg", "Germany", 1899000, 53.5511, 9.9937, "major", 755, 2516, 48000, 4.6, 27.8),
            ("Naples", "Italy", 967000, 40.8518, 14.2681, "major", 117, 8267, 29000, 15.4, 8.9),
            ("Turin", "Italy", 870000, 45.0703, 7.6869, "major", 130, 6692, 38000, 8.7, 14.2),
            ("Cologne", "Germany", 1087000, 50.9375, 6.9603, "major", 405, 2686, 47000, 5.1, 22.1),
            ("Frankfurt", "Germany", 753000, 50.1109, 8.6821, "major", 248, 3037, 71000, 4.2, 18.5),
            ("Rotterdam", "Netherlands", 651000, 51.9244, 4.4777, "major", 206, 3162, 45000, 7.8, 19.7),
            ("Valencia", "Spain", 791000, 39.4699, -0.3763, "regional", 135, 5863, 31000, 11.2, 16.8),
            ("Seville", "Spain", 688000, 37.3891, -5.9845, "regional", 140, 4915, 29000, 13.1, 22.1),
            ("Lyon", "France", 515000, 45.7640, 4.8357, "regional", 47, 10957, 41000, 7.3, 25.3),

            # Additional regional cities
            ("Marseille", "France", 870000, 43.2965, 5.3698, "major", 241, 3609, 35000, 9.8, 12.4),
            ("Toulouse", "France", 479000, 43.6047, 1.4442, "regional", 118, 4060, 39000, 6.7, 19.8),
            ("Nice", "France", 342000, 43.7102, 7.2620, "regional", 72, 4750, 42000, 8.4, 13.2),
            ("Bordeaux", "France", 254000, 44.8378, -0.5792, "regional", 49, 5184, 43000, 7.1, 33.1),
            ("Nantes", "France", 309000, 47.2184, -1.5536, "regional", 65, 4754, 41000, 6.9, 37.8),
            ("Strasbourg", "France", 280000, 48.5734, 7.7521, "regional", 78, 3590, 38000, 8.2, 26.7),
            ("Lille", "France", 232000, 50.6292, 3.0573, "regional", 35, 6629, 35000, 11.4, 14.5),
            ("Rennes", "France", 217000, 48.1173, -1.6778, "regional", 50, 4340, 40000, 6.8, 42.1),
            ("Montpellier", "France", 285000, 43.6110, 3.8767, "regional", 57, 5000, 37000, 9.3, 21.8),
            ("Grenoble", "France", 158000, 45.1885, 5.7245, "regional", 18, 8778, 36000, 8.9, 20.3),

            # German cities
            ("Stuttgart", "Germany", 626000, 48.7758, 9.1829, "major", 207, 3024, 51000, 4.8, 24.7),
            ("Düsseldorf", "Germany", 619000, 51.2277, 6.7735, "major", 217, 2853, 58000, 5.6, 19.2),
            ("Dortmund", "Germany", 588000, 51.5136, 7.4653, "major", 280, 2100, 41000, 8.9, 26.8),
            ("Essen", "Germany", 583000, 51.4556, 7.0116, "major", 210, 2777, 39000, 9.7, 23.4),
            ("Leipzig", "Germany", 587000, 51.3397, 12.3731, "major", 297, 1977, 38000, 7.3, 31.2),
            ("Bremen", "Germany", 569000, 53.0793, 8.8017, "major", 325, 1751, 44000, 6.1, 21.8),
            ("Dresden", "Germany", 556000, 51.0504, 13.7373, "major", 328, 1695, 42000, 5.8, 34.6),
            ("Hanover", "Germany", 535000, 52.3759, 9.7320, "major", 204, 2623, 46000, 6.4, 19.7),
            ("Nuremberg", "Germany", 518000, 49.4521, 11.0767, "major", 186, 2785, 43000, 5.2, 24.1),
            ("Duisburg", "Germany", 498000, 51.4344, 6.7623, "regional", 233, 2138, 37000, 11.2, 16.3),

            # UK cities
            ("Birmingham", "United Kingdom", 1141000, 52.4862, -1.8904, "major", 268, 4259, 29000, 7.8, 15.4),
            ("Leeds", "United Kingdom", 789000, 53.8008, -1.5491, "major", 552, 1430, 32000, 4.2, 19.7),
            ("Glasgow", "United Kingdom", 635000, 55.8642, -4.2518, "major", 175, 3629, 31000, 6.8, 20.1),
            ("Sheffield", "United Kingdom", 584000, 53.3811, -1.4701, "major", 368, 1587, 28000, 4.3, 22.6),
            ("Bradford", "United Kingdom", 537000, 53.7960, -1.7594, "regional", 366, 1467, 25000, 5.9, 13.8),
            ("Edinburgh", "United Kingdom", 524000, 55.9533, -3.1883, "capital", 264, 1985, 38000, 3.4, 26.3),
            ("Liverpool", "United Kingdom", 498000, 53.4084, -2.9916, "major", 111, 4486, 27000, 8.7, 17.9),
            ("Manchester", "United Kingdom", 547000, 53.4808, -2.2426, "major", 116, 4716, 33000, 6.2, 18.5),

            # Italian cities
            ("Palermo", "Italy", 673000, 38.1157, 13.3615, "regional", 158, 4259, 24000, 18.3, 11.2),
            ("Genoa", "Italy", 580000, 44.4056, 8.9463, "major", 243, 2387, 35000, 9.1, 15.7),
            ("Bologna", "Italy", 389000, 44.4949, 11.3426, "major", 141, 2760, 41000, 4.8, 28.4),
            ("Florence", "Italy", 383000, 43.7696, 11.2558, "major", 102, 3756, 38000, 6.3, 20.1),
            ("Bari", "Italy", 320000, 41.1171, 16.8719, "regional", 117, 2735, 26000, 11.7, 8.9),
            ("Catania", "Italy", 311000, 37.5079, 15.0830, "regional", 180, 1728, 23000, 15.8, 7.3),

            # Spanish cities
            ("Zaragoza", "Spain", 675000, 41.6488, -0.8891, "regional", 974, 693, 32000, 10.4, 18.7),
            ("Málaga", "Spain", 574000, 36.7213, -4.4214, "regional", 395, 1453, 30000, 16.2, 12.3),
            ("Murcia", "Spain", 453000, 37.9922, -1.1307, "regional", 882, 514, 28000, 12.8, 19.4),
            ("Palma", "Spain", 416000, 39.5696, 2.6502, "regional", 209, 1991, 34000, 8.7, 14.8),
            ("Las Palmas", "Spain", 379000, 28.1248, -15.4300, "regional", 101, 3752, 27000, 13.4, 11.6),
            ("Bilbao", "Spain", 346000, 43.2627, -2.9253, "regional", 41, 8439, 36000, 9.8, 21.7),

            # Other European cities
            ("Thessaloniki", "Greece", 325000, 40.6401, 22.9444, "major", 19, 17105, 22000, 17.1, 8.4),
            ("Athens", "Greece", 664000, 37.9755, 23.7348, "capital", 39, 17026, 24000, 16.8, 9.2),
            ("Porto", "Portugal", 238000, 41.1579, -8.6291, "major", 41, 5805, 28000, 8.9, 16.3),
            ("Braga", "Portugal", 193000, 41.5518, -8.4229, "regional", 184, 1049, 25000, 7.2, 35.7),
            ("Rotterdam", "Netherlands", 651000, 51.9244, 4.4777, "major", 206, 3162, 45000, 7.8, 19.7),
            ("The Hague", "Netherlands", 545000, 52.0705, 4.3007, "major", 98, 5561, 52000, 4.1, 27.8),
            ("Utrecht", "Netherlands", 357000, 52.0907, 5.1214, "major", 99, 3606, 47000, 3.8, 22.4),
            ("Eindhoven", "Netherlands", 234000, 51.4416, 5.4697, "regional", 88, 2659, 41000, 5.4, 18.6),
        ]

        created_count = 0
        updated_count = 0

        # Add the base European cities
        for name, country, pop, lat, lng, city_type, area, density, gdp, unemployment, green_space in european_cities_data:
            if created_count >= count:
                break

            try:
                city, created = City.objects.get_or_create(
                    name=name,
                    country=country,
                    defaults={
                        'population': pop,
                        'latitude': lat,
                        'longitude': lng,
                        'location': Point(lng, lat, srid=4326),
                        'city_type': city_type,
                        'urban_area_km2': area,
                        'population_density': density,
                        'gdp_per_capita': gdp,
                        'unemployment_rate': unemployment,
                        'green_space_percentage': green_space,
                        'elevation': random.randint(0, 500),
                        'region_code': f"{country[:2].upper()}{random.randint(10, 99)}",
                        'population_year': random.choice([2022, 2023]),
                        'data_source': 'European Urban Planning Agency'
                    }
                )

                if created:
                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f" Created: {name}, {country}")
                    )
                else:
                    updated_count += 1
                    self.stdout.write(
                        self.style.WARNING(f"  Already exists: {name}, {country}")
                    )

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f" Error creating {name}: {e}")
                )

        # Generate additional random cities if needed
        if created_count < count:
            additional_needed = count - created_count
            self.stdout.write(f"Generating {additional_needed} additional cities...")

            # Check what fields actually exist in the model
            model_fields = [field.name for field in City._meta.get_fields()]
            self.stdout.write(f"Available model fields: {model_fields}")

            countries = ["Germany", "France", "Italy", "Spain", "Poland", "United Kingdom", 
                        "Netherlands", "Belgium", "Czech Republic", "Hungary", "Austria", 
                        "Sweden", "Denmark", "Finland", "Norway", "Portugal", "Greece"]

            city_types = ["regional", "town", "major"]

            for i in range(additional_needed):
                country = random.choice(countries)
                city_name = f"City_{random.randint(1000, 9999)}"

                # Generate realistic European coordinates
                lat = random.uniform(35.0, 70.0)  # European latitude range
                lng = random.uniform(-10.0, 30.0)  # European longitude range

                population = random.randint(50000, 1500000)
                area = random.uniform(20, 800)

                try:
                    # Use get_or_create and only include fields that exist
                    city_data = {
                        'population': population,
                        'latitude': lat,
                        'longitude': lng,
                        'location': Point(lng, lat, srid=4326),
                        'city_type': random.choice(city_types),
                    }

                    # Only add fields if they exist in the model
                    if 'urban_area_km2' in model_fields:
                        city_data['urban_area_km2'] = area
                    if 'population_density' in model_fields:
                        city_data['population_density'] = population / area
                    if 'gdp_per_capita' in model_fields:
                        city_data['gdp_per_capita'] = random.randint(20000, 70000)
                    if 'unemployment_rate' in model_fields:
                        city_data['unemployment_rate'] = random.uniform(2.0, 15.0)
                    if 'green_space_percentage' in model_fields:
                        city_data['green_space_percentage'] = random.uniform(8.0, 45.0)
                    if 'elevation' in model_fields:
                        city_data['elevation'] = random.randint(0, 800)
                    if 'region_code' in model_fields:
                        city_data['region_code'] = f"{country[:2].upper()}{random.randint(10, 99)}"
                    if 'population_year' in model_fields:
                        city_data['population_year'] = random.choice([2022, 2023])
                    if 'data_source' in model_fields:
                        city_data['data_source'] = 'Generated Data'

                    city, created = City.objects.get_or_create(
                        name=city_name,
                        country=country,
                        defaults=city_data
                    )

                    if created:
                        created_count += 1
                        if created_count % 10 == 0:
                            self.stdout.write(f"Generated {created_count}/{count} cities...")
                    else:
                        self.stdout.write(f"City {city_name} already exists")

                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f" Error generating city {city_name}: {e}")
                    )

        self.stdout.write(
            self.style.SUCCESS(
                f'\n🎉 City population complete!'
                f'\nCreated: {created_count}'
                f'\nExisting: {updated_count}'
                f'\nTotal cities in database: {City.objects.count()}'
            )
        )