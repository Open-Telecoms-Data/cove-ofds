from django import forms
from django.conf import settings


class NewGeoJSONUploadForm(forms.Form):
    nodes_file_upload = forms.FileField(
        widget=forms.FileInput(
            attrs={
                "accept": ",".join(
                    settings.ALLOWED_GEOJSON_CONTENT_TYPES
                    + settings.ALLOWED_GEOJSON_EXTENSIONS
                )
            }
        )
    )
    spans_file_upload = forms.FileField(
        widget=forms.FileInput(
            attrs={
                "accept": ",".join(
                    settings.ALLOWED_GEOJSON_CONTENT_TYPES
                    + settings.ALLOWED_GEOJSON_EXTENSIONS
                )
            }
        )
    )
