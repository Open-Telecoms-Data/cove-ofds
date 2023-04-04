from django.core.management.base import BaseCommand

from libcoveweb2.background_worker import process_supplied_data
from libcoveweb2.models import SuppliedData


class Command(BaseCommand):
    help = "Reprocess all the supplied data we can (everything not expired)"

    def handle(self, *args, **options):
        for supplied_data in SuppliedData.objects.filter(expired__isnull=True):
            if supplied_data.processed:
                supplied_data.processed = None
                supplied_data.save()
            process_supplied_data(supplied_data.id)
