import json
import os

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

from libcoveweb2.process.base import ProcessDataTask


class TaskWithState(ProcessDataTask):
    """An abstract task that helps you save state from the processing step and add it to the context.
    Extend and provide your own state_filename and process_get_state.
    """

    """Set state_filename to a unique name for each task.
    If you change this name the task will be rerun, so this is is a good way to
    make sure all underlying data changes if a new version of this bit of cove is released."""
    state_filename: str = "task_with_state.py"

    def process_get_state(self, process_data: dict):
        """Should return a dict that is the state to save, and process_data.
        Is only called if there is work to do, so does not need to worry about checking that."""
        return {}, process_data

    def process(self, process_data: dict) -> dict:
        if self.does_state_exist():
            return process_data

        state, process_data = self.process_get_state(process_data)

        default_storage.save(
            os.path.join(self.supplied_data.storage_dir(), self.state_filename),
            ContentFile(json.dumps(state, indent=4)),
        )

        return process_data

    def does_state_exist(self) -> bool:
        return default_storage.exists(
            os.path.join(self.supplied_data.storage_dir(), self.state_filename)
        )

    def is_processing_applicable(self) -> bool:
        return True

    def is_processing_needed(self) -> bool:
        return not self.does_state_exist()

    def get_context(self):
        if self.does_state_exist():
            with default_storage.open(
                os.path.join(self.supplied_data.storage_dir(), self.state_filename)
            ) as fp:
                return json.load(fp)
        else:
            return {}
