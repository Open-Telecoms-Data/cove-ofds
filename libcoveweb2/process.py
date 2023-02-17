class ProcessDataTask:
    def __init__(self, supplied_data):
        self.supplied_data = supplied_data

    def process(self, process_data: dict) -> dict:
        return process_data

    def get_context(self):
        return {}



class ProcessDataTaskException(Exception):
    def __init__(self, template_name: str, template_vars: dict, original_exception: Exception):
        self.template_name = template_name
        self.template_vars = template_vars
        self.original_exception = original_exception