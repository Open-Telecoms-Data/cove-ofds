import os
import urllib.parse
import uuid

import requests
from django.conf import settings
from django.db import models
from django.urls import reverse


class SuppliedData(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    format = models.TextField()

    created = models.DateTimeField(auto_now_add=True, null=True)
    expired = models.DateTimeField(null=True)

    def data_dir(self):
        return os.path.join(settings.MEDIA_ROOT, str(self.id))

    def data_url(self):
        return os.path.join(settings.MEDIA_URL, str(self.id))

    def upload_dir(self):
        return os.path.join(settings.MEDIA_ROOT, str(self.id), "supplied_data")

    def upload_url(self):
        return os.path.join(settings.MEDIA_URL, str(self.id), "supplied_data")

    def get_absolute_url(self):
        return reverse("explore", args=(self.pk,))

    def save_file(self, f, meta={}, source_method: str = "upload"):
        os.makedirs(self.upload_dir(), exist_ok=True)

        supplied_data_file = SuppliedDataFile()
        supplied_data_file.supplied_data = self
        supplied_data_file.filename = f.name
        supplied_data_file.size = f.size
        supplied_data_file.content_type = f.content_type
        supplied_data_file.charset = f.charset
        supplied_data_file.meta = meta
        supplied_data_file.source_method = source_method
        supplied_data_file.save()

        with open(supplied_data_file.upload_dir_and_filename(), "wb+") as destination:
            for chunk in f.chunks():
                destination.write(chunk)

    def save_file_contents(
        self,
        filename: str,
        contents: str,
        content_type: str,
        charset: str = None,
        meta: dict = {},
        source_method: str = "text",
    ):

        os.makedirs(self.upload_dir(), exist_ok=True)

        supplied_data_file = SuppliedDataFile()
        supplied_data_file.supplied_data = self
        supplied_data_file.filename = filename
        supplied_data_file.size = len(contents)
        supplied_data_file.content_type = content_type
        supplied_data_file.charset = charset
        supplied_data_file.meta = meta
        supplied_data_file.source_method = source_method
        supplied_data_file.save()

        with open(supplied_data_file.upload_dir_and_filename(), "w") as destination:
            destination.write(contents)

    def save_file_from_source_url(
        self, url: str, meta: dict = {}, source_method: str = "url", content_type=None
    ):

        url_bits = urllib.parse.urlparse(url)
        path_bits = url_bits.path.split("/") if url_bits.path else ["data"]
        filename = path_bits.pop()

        supplied_data_file = SuppliedDataFile()
        supplied_data_file.supplied_data = self
        supplied_data_file.filename = filename
        supplied_data_file.source_url = url
        supplied_data_file.content_type = content_type
        supplied_data_file.meta = meta
        supplied_data_file.source_method = source_method
        supplied_data_file.save()


class SuppliedDataFile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    supplied_data = models.ForeignKey(SuppliedData, on_delete=models.CASCADE)
    filename = models.TextField()
    size = models.PositiveBigIntegerField(null=True)
    content_type = models.TextField(null=True)
    charset = models.TextField(null=True)
    meta = models.JSONField(null=True)
    source_method = models.TextField(null=True)
    source_url = models.URLField(null=True)

    def upload_dir_and_filename(self):
        return os.path.join(
            self.supplied_data.upload_dir(), str(self.id) + "-" + self.filename
        )

    def upload_url(self):
        return os.path.join(
            settings.MEDIA_URL,
            str(self.supplied_data.id),
            "supplied_data",
            self.upload_filename(),
        )

    def upload_filename(self):
        return str(self.id) + "-" + self.filename

    def does_exist_in_storage(self):
        return os.path.exists(self.upload_dir_and_filename())

    def is_download_from_source_url_needed(self) -> bool:
        return (
            not self.supplied_data.expired
            and self.source_url
            and not os.path.exists(self.upload_dir_and_filename())
        )

    def download_from_source_url(self):
        # Make dir
        os.makedirs(self.supplied_data.upload_dir(), exist_ok=True)
        # Upload
        request_headers = {"User-Agent": "Cove (cove.opendataservice.coop)"}
        with requests.get(self.source_url, stream=True, headers=request_headers) as r:
            # Errors? TODO better return
            r.raise_for_status()
            # Save
            with open(self.upload_dir_and_filename(), "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
            # Update record
            self.size = os.path.getsize(self.upload_dir_and_filename())
            self.charset = r.encoding
            if not self.content_type:
                self.content_type = r.headers.get("content-type")
            self.save()
