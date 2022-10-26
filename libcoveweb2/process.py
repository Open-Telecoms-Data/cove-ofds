class ProcessDataTask:
    def __init__(self, supplied_data):
        self.supplied_data = supplied_data

    def process(self, process_data: dict) -> dict:
        return process_data

    def get_context(self):
        return {}
