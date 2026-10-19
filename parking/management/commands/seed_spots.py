from django.core.management.base import BaseCommand, CommandError
from parking.models import Spot
class Command(BaseCommand):
    help = 'Add parking spots without deleting existing spots or visits.'
    def add_arguments(self, parser):
        parser.add_argument('--count', type=int, default=24)
    def handle(self, *args, **options):
        count = options['count']
        if not 1 <= count <= 200:
            raise CommandError('Choose 1–200 spots.')
        for i in range(count):
            Spot.objects.get_or_create(label=f'{chr(65+i//8)}{i%8+1:02}')
        self.stdout.write(self.style.SUCCESS(f'{Spot.objects.count()} spots available in the database.'))
