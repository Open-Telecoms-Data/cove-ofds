from django import forms
from django.conf import settings


class NewJSONUploadForm(forms.Form):
    file_field_names = ["file_upload"]
    file_upload = forms.FileField(
        widget=forms.FileInput(
            attrs={
                "accept": ",".join(
                    settings.ALLOWED_JSON_CONTENT_TYPES
                    + settings.ALLOWED_JSON_EXTENSIONS
                )
            }
        ),
        label="",
    )


class NewJSONTextForm(forms.Form):
    file_field_names = []
    paste = forms.CharField(label="Paste (JSON only)", widget=forms.Textarea)


class NewJSONURLForm(forms.Form):
    file_field_names = []
    url = forms.URLField(label="URL")


class NewSpreadsheetUploadForm(forms.Form):
    file_field_names = ["file_upload"]
    file_upload = forms.FileField(
        label="",
        widget=forms.FileInput(
            attrs={
                "accept": ",".join(
                    settings.ALLOWED_SPREADSHEET_CONTENT_TYPES
                    + settings.ALLOWED_SPREADSHEET_EXTENSIONS
                )
            }
        ),
    )


class NewCSVsUploadForm(forms.Form):
    # I know it's hacky to copy and paste code like this but as this needs to be replaced by
    # something that allows any number of uploads with no limits this will do for now
    file_field_names = ["file_upload" + str(i) for i in range(0, 10)]
    file_upload0 = forms.FileField(
        label="",
        widget=forms.FileInput(
            attrs={
                "accept": ",".join(
                    settings.ALLOWED_CSV_CONTENT_TYPES + settings.ALLOWED_CSV_EXTENSIONS
                )
            }
        ),
    )
    file_upload1 = forms.FileField(
        label="",
        widget=forms.FileInput(
            attrs={
                "accept": ",".join(
                    settings.ALLOWED_CSV_CONTENT_TYPES + settings.ALLOWED_CSV_EXTENSIONS
                )
            }
        ),
        required=False,
    )
    file_upload2 = forms.FileField(
        label="",
        widget=forms.FileInput(
            attrs={
                "accept": ",".join(
                    settings.ALLOWED_CSV_CONTENT_TYPES + settings.ALLOWED_CSV_EXTENSIONS
                )
            }
        ),
        required=False,
    )
    file_upload3 = forms.FileField(
        label="",
        widget=forms.FileInput(
            attrs={
                "accept": ",".join(
                    settings.ALLOWED_CSV_CONTENT_TYPES + settings.ALLOWED_CSV_EXTENSIONS
                )
            }
        ),
        required=False,
    )
    file_upload4 = forms.FileField(
        label="",
        widget=forms.FileInput(
            attrs={
                "accept": ",".join(
                    settings.ALLOWED_CSV_CONTENT_TYPES + settings.ALLOWED_CSV_EXTENSIONS
                )
            }
        ),
        required=False,
    )
    file_upload5 = forms.FileField(
        label="",
        widget=forms.FileInput(
            attrs={
                "accept": ",".join(
                    settings.ALLOWED_CSV_CONTENT_TYPES + settings.ALLOWED_CSV_EXTENSIONS
                )
            }
        ),
        required=False,
    )
    file_upload6 = forms.FileField(
        label="",
        widget=forms.FileInput(
            attrs={
                "accept": ",".join(
                    settings.ALLOWED_CSV_CONTENT_TYPES + settings.ALLOWED_CSV_EXTENSIONS
                )
            }
        ),
        required=False,
    )
    file_upload7 = forms.FileField(
        label="",
        widget=forms.FileInput(
            attrs={
                "accept": ",".join(
                    settings.ALLOWED_CSV_CONTENT_TYPES + settings.ALLOWED_CSV_EXTENSIONS
                )
            }
        ),
        required=False,
    )
    file_upload8 = forms.FileField(
        label="",
        widget=forms.FileInput(
            attrs={
                "accept": ",".join(
                    settings.ALLOWED_CSV_CONTENT_TYPES + settings.ALLOWED_CSV_EXTENSIONS
                )
            }
        ),
        required=False,
    )
    file_upload9 = forms.FileField(
        label="",
        widget=forms.FileInput(
            attrs={
                "accept": ",".join(
                    settings.ALLOWED_CSV_CONTENT_TYPES + settings.ALLOWED_CSV_EXTENSIONS
                )
            }
        ),
        required=False,
    )


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
