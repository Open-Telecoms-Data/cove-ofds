from django import forms
from django.conf import settings


class NewGeoJSONUploadForm(forms.Form):
    nodes_file_upload = forms.FileField(
        label="Nodes file",
        widget=forms.FileInput(
            attrs={
                "accept": ",".join(
                    settings.ALLOWED_GEOJSON_CONTENT_TYPES
                    + settings.ALLOWED_GEOJSON_EXTENSIONS
                )
            }
        ),
        required=False,
    )
    spans_file_upload = forms.FileField(
        label="Spans file",
        widget=forms.FileInput(
            attrs={
                "accept": ",".join(
                    settings.ALLOWED_GEOJSON_CONTENT_TYPES
                    + settings.ALLOWED_GEOJSON_EXTENSIONS
                )
            }
        ),
        required=False,
    )


class NewGeoJSONURLForm(forms.Form):
    nodes_file_url = forms.URLField(
        label="Nodes URL",
        required=False,
    )
    spans_file_url = forms.URLField(
        label="Spans URL",
        required=False,
    )
