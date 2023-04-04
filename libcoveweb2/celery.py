import os

from celery import Celery

# set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cove_project.settings")

# Create Celery App
app = Celery("tasks")

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object("django.conf:settings", namespace="CELERY")

app.conf.update(
    # Set so producer of messages will eventually time out and not try for ever
    # This shouldn't ever apply on live; 20 is such a big number
    # But it might apply if tests are ever run badly, and without this your tests is stuck in an infinte loop
    #   (not great when it's run on someone's C.I.!)
    broker_transport_options={"max_retries": 20},
)
# Load task modules from all registered Django app configs.
app.autodiscover_tasks()


class CeleryInspector:
    def __init__(self):
        global app
        self._inspector = app.control.inspect()

    def is_supplied_data_being_processed(self, id):
        data = self._inspector.active()
        for worker, tasks in data.items():
            for task in tasks:
                if task.get("args", [])[0] == str(id):
                    return True
        return False
