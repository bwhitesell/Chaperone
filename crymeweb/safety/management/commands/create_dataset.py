import datetime
from django.core.management.base import BaseCommand
import random
import numpy as np
import sys

from regions.models import GeometricRegion
from safety.models import SyntheticAnalysisRequest


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            '--guarantee',
            action='store_true',
            help='Guarantee the command.',
        )

        parser.add_argument(
            'n_samples',
            type=int,
            default=500,
            help='Number of samples to generate.',
        )

    def handle(self, *args, **options):
        if not options['guarantee']:
            sys.exit(1)

        gd = GeometricRegion.objects.first()
        min_lat, max_lat, min_long, max_long = gd.get_bounding_box()
        dataset = self.generate_location_times(min_lat, max_lat, min_long, max_long, 365, gd, options['n_samples'])
        SyntheticAnalysisRequest.objects.bulk_create(
            [SyntheticAnalysisRequest(longitude=row[0], latitude=row[1], timestamp=row[2]) for row in dataset]
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
                ts = datetime.datetime.now() - datetime.timedelta(
                    days=random.uniform(5, td_size))
                samples.append([long, lat, ts])
                length = len(samples)
                if length % 1000 == 0:
                    print(f'{length} samples generated...')

        return np.array(samples)
