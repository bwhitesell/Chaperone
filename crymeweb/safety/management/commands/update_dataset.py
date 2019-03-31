from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.db.models import Max
''
import random
import numpy as np
import sys

from regions.models import GeometricRegion
from safety.models import SafetyAnalysisRequest


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            '--guarantee',
            action='store_true',
            help='Gaurantee the command.',
        )

        parser.add_argument(
            'samples_per_day',
            type=int,
            default=500,
            help='Number of samples to generate.',
        )

    def handle(self, *args, **options):
        if not options['guarantee']:
            sys.exit(1)

        gd = GeometricRegion.objects.first()
        min_lat, max_lat, min_long, max_long = gd.get_bounding_box()
        most_recent_ts = SafetyAnalysisRequest.objects.all().aggregate(Max('timestamp'))['timestamp__max']
        td_size = (datetime.now() - most_recent_ts).total_seconds() / timedelta(days=1).total_seconds()
        n_samples = td_size * options['samples_per_day']
        dataset = self.generate_location_times(min_lat, max_lat, min_long, max_long, td_size, gd, n_samples)
        SafetyAnalysisRequest.objects.bulk_create(
            [SafetyAnalysisRequest(longitude=row[0], latitude=row[1], timestamp=row[2]) for row in dataset]
        )

    @staticmethod
    def generate_location_times(min_lat, max_lat, min_long, max_long, td_size, domain, n_samples):
        samples = []
        length = 0
        gd = domain
        while length < n_samples:
            lat = random.uniform(min_lat, max_lat)
            long = random.uniform(min_long, max_long)
            if gd.in_domain(long, lat):
                ts = datetime.now() - timedelta(
                    days=random.uniform(0, td_size))
                samples.append([long, lat, ts])
                length = len(samples)
                if length % 1000 == 0:
                    print(f'{length} samples generated...')

        return np.array(samples)
