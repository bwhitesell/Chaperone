from django.core.management.base import BaseCommand
import sys


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            '--guarantee',
            action='store_true',
            help='Gaurantee the command.',
        )

    def handle(self, *args, **options):
        if not options['guarantee']:
            sys.exit(1)

        print('hi')
