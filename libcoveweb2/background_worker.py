import logging

from libcoveweb2.celery import app
from libcoveweb2.process import process_data_worker

logger = logging.getLogger(__name__)


def process_supplied_data(id: str):
    """Call to process some supplied data.
    Sends processing work to a worker so calling thread will get a return immediately
    (if Celery is configured properly)."""
    logger.info("Adding to Queue - process supplied data id " + str(id))
    _process_supplied_data_celery_task.delay(id)


@app.task
def _process_supplied_data_celery_task(id: str):
    process_data_worker(id)
