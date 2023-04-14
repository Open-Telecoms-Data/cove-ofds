from libcoveweb2.models import SuppliedData


class ProcessDataTask:
    """Base class for a task to apply to some user supplied data."""

    def __init__(self, supplied_data: SuppliedData):
        self.supplied_data: SuppliedData = supplied_data

    def is_processing_applicable(self) -> bool:
        """Should return True if this task may ever need to do anything far this supplied data.

        eg. A task to convert a spreadsheet to JSON will never be applicable if JSON is uploaded in the first place.
        eg. A task to check the data against JSON Schema will always be applicable.
        """
        return False

    def is_processing_needed(self) -> bool:
        """Should return True if this task needs to do any processing"""
        return False

    def process(self, process_data: dict) -> dict:
        """Called to process data.

        This takes in a dict, process_data, and it should always return this dict.
        This dict starts as an empty dict at the start of the pipeline.
        Tasks at the start of the pipeline may add useful information that tasks at the end of the pipeline can use.

        Note this is always called when processing data even if is_processing_needed returns False.
        You should do your own checks to make sure you are not doing unneeded work.
        This is so you can still add relevant info to process_data dict.

        But it's not called if is_processing_applicable() is false."""
        return process_data

    def get_context(self):
        """Load all relevant data for this task and return it in a dict.
        This will be passed to the explore template when the user looks at some data.

        This is called on a user request on the web, so no long processing work should be done here.
        Instead, do long processing work in process() and cache the results."""
        return {}
