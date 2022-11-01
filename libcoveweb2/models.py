import os
import uuid

from django.conf import settings
from django.db import models
from django.urls import reverse


class SuppliedData(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    format = models.TextField()

    created = models.DateTimeField(auto_now_add=True, null=True)

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

    def save_file(self, f):
        os.makedirs(self.upload_dir(), exist_ok=True)

        supplied_data_file = SuppliedDataFile()
        supplied_data_file.supplied_data = self
        supplied_data_file.filename = f.name
        supplied_data_file.size = f.size
        supplied_data_file.content_type = f.content_type
        supplied_data_file.charset = f.charset
        supplied_data_file.save()

        with open(supplied_data_file.upload_dir_and_filename(), "wb+") as destination:
            for chunk in f.chunks():
                destination.write(chunk)


class SuppliedDataFile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    supplied_data = models.ForeignKey(SuppliedData, on_delete=models.CASCADE)
    filename = models.TextField()
    size = models.PositiveBigIntegerField()
    content_type = models.TextField(null=True)
    charset = models.TextField(null=True)

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
