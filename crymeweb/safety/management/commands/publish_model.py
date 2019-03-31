from datetime import datetime
from django.core.management.base import BaseCommand
import sys

from safety.models import SafetyModel


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            '--guarantee',
            action='store_true',
            help='Guarantee the command.',
        )

        parser.add_argument(
            'name',
            type=str,
            default='CrymeClassifier',
            help='The name of the model being published.',
        )

        parser.add_argument(
            'version',
            type=str,
            help='The version number of the model being published',
        )

        parser.add_argument(
            'type',
            type=str,
            help='The type model being published',
        )

    def handle(self, *args, **options):
        if not options['guarantee']:
            sys.exit(1)

        # remove the current status from any models of identical type.
        for model in SafetyModel.objects.filter(pred_type=options['type']):
            model.current = False
            model.save()

        # create a new model record and set it to current.
        SafetyModel.objects.create(
            name=options['name'],
            version=options['version'],
            pred_type=options['type'],
            publish_timestamp=datetime.now(),
            current=True
        )
