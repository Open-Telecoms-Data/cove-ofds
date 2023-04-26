import importlib
import logging
import sys
import traceback
from datetime import datetime

from django.conf import settings
from django.core.exceptions import ValidationError
from sentry_sdk import capture_exception

from libcoveweb2.models import SuppliedData, SuppliedDataFile

logger = logging.getLogger(__name__)


def get_tasks(supplied_data: SuppliedData):
    """Get a list of instantiated task classes far a piece of supplied data, ready to use."""
    supplied_data_files = SuppliedDataFile.objects.filter(supplied_data=supplied_data)
    return [
        getattr(importlib.import_module(m), c)(supplied_data, supplied_data_files)
        for m, c in settings.PROCESS_TASKS
    ]


def process_data_worker(id: str):
    """Processes all relevant tasks for a bit of supplied data. Works in same thread as calling code.
    Pass id as string, not data abject."""
    logger.info("Processing supplied data id " + str(id))

    # ------ Get data, check we can work on it
    try:
        supplied_data: SuppliedData = SuppliedData.objects.get(pk=id)
    except (
        SuppliedData.DoesNotExist,
        ValidationError,
    ):  # Catches primary key does not exist and badly formed UUID
        return
    if supplied_data.expired or supplied_data.processed:
        return

    # ------ Get our tasks
    tasks = get_tasks(supplied_data)

    # ------ Run tasks!
    try:
        process_data = {}
        for task in tasks:
            if task.is_processing_applicable():
                process_data = task.process(process_data)
    except Exception as e:
        # To our database
        supplied_data.error = str(e)
        # To logs
        exc_type, exc_value, exc_traceback = sys.exc_info()
        logger.error(traceback.print_exception(exc_type, exc_value, exc_traceback))
        # To Sentry
        capture_exception(e)

    # ------ Save result
    supplied_data.processed = datetime.now()
    supplied_data.save()
