from libcoveweb2.process.base import ProcessDataTask


class DownloadDataTask(ProcessDataTask):
    """If user gave us a URL, we download it now."""

    def is_processing_applicable(self) -> bool:
        for supplied_data_file in self.supplied_data_files:
            if supplied_data_file.source_url:
                return True
        return False

    def is_processing_needed(self) -> bool:
        for supplied_data_file in self.supplied_data_files:
            if supplied_data_file.is_download_from_source_url_needed():
                return True
        return False

    def process(self, process_data: dict) -> dict:
        for supplied_data_file in self.supplied_data_files:
            if supplied_data_file.is_download_from_source_url_needed():
                supplied_data_file.download_from_source_url()

        return process_data
