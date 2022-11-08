import shutil
from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from libcoveweb2.models import SuppliedData


class Command(BaseCommand):
    help = "Delete files that are older than a number of days (DELETE_FILES_AFTER_DAYS setting)"

    def handle(self, *args, **options):
        old_data = SuppliedData.objects.filter(
            created__lt=timezone.now()
            - timedelta(days=getattr(settings, "DELETE_FILES_AFTER_DAYS", 7))
        )
        for supplied_data in old_data:
            try:
                shutil.rmtree(supplied_data.data_dir())
            except FileNotFoundError:
                continue
