import importlib
import logging
from datetime import datetime

from django.conf import settings
from django.core.exceptions import ValidationError

from libcoveweb2.models import SuppliedData

logger = logging.getLogger(__name__)


def get_tasks(supplied_data: SuppliedData):
    """Get a list of instantiated task classes far a piece of supplied data, ready to use."""
    return [
        getattr(importlib.import_module(m), c)(supplied_data)
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
    process_data = {}
    for task in tasks:
        if task.is_processing_applicable():
            process_data = task.process(process_data)

    # ------ Save result
    supplied_data.processed = datetime.now()
    supplied_data.save()
