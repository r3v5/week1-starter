import time

from django.contrib.gis.geos import Point
from django.core.management.base import BaseCommand

from cities_api.models import City
from cities_api.views import cities_within_radius_queryset, nearest_cities_queryset

TEST_POINTS = {
    "Dublin": (53.3498, -6.2603),
    "London": (51.5074, -0.1278),
    "Paris": (48.8566, 2.3522),
    "New York": (40.7128, -74.0060),
    "Tokyo": (35.6762, 139.6503),
}


class Command(BaseCommand):
    help = "Time the nearest-city and radius queries used by the proximity API"

    def add_arguments(self, parser):
        parser.add_argument("--iterations", type=int, default=50)
        parser.add_argument("--radius-km", type=float, default=1000)

    def time_query(self, build_query, iterations):
        # Evaluate once first so connection setup is not counted.
        list(build_query())
        start = time.perf_counter()
        for _ in range(iterations):
            results = list(build_query())
        elapsed_ms = (time.perf_counter() - start) * 1000 / iterations
        return elapsed_ms, len(results)

    def handle(self, *args, **options):
        iterations = options["iterations"]
        radius_km = options["radius_km"]
        self.stdout.write(
            f"Cities with locations: {City.objects.filter(location__isnull=False).count()}"
        )
        self.stdout.write(f"Iterations per query: {iterations}, radius: {radius_km} km\n")

        nearest_times, radius_times = [], []
        for name, (lat, lng) in TEST_POINTS.items():
            point = Point(lng, lat, srid=4326)
            nearest_ms, nearest_count = self.time_query(
                lambda: nearest_cities_queryset(point), iterations
            )
            radius_ms, radius_count = self.time_query(
                lambda: cities_within_radius_queryset(point, radius_km), iterations
            )
            nearest_times.append(nearest_ms)
            radius_times.append(radius_ms)
            self.stdout.write(
                f"{name:<10} nearest: {nearest_ms:6.2f} ms ({nearest_count} results)   "
                f"radius: {radius_ms:6.2f} ms ({radius_count} results)"
            )

        self.stdout.write(self.style.SUCCESS(
            f"\nAverage nearest query: {sum(nearest_times) / len(nearest_times):.2f} ms"
        ))
        self.stdout.write(self.style.SUCCESS(
            f"Average radius query:  {sum(radius_times) / len(radius_times):.2f} ms"
        ))

        dublin = Point(TEST_POINTS["Dublin"][1], TEST_POINTS["Dublin"][0], srid=4326)
        self.stdout.write("\nNearest query plan (Dublin):")
        self.stdout.write(nearest_cities_queryset(dublin).explain(analyze=True))
        self.stdout.write(f"\nRadius query plan (Dublin, {radius_km} km):")
        self.stdout.write(cities_within_radius_queryset(dublin, radius_km).explain(analyze=True))
