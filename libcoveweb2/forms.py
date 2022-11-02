from django import forms

from libcoveweb2.settings import (
    ALLOWED_JSON_CONTENT_TYPES,
    ALLOWED_JSON_EXTENSIONS,
    ALLOWED_SPREADSHEET_CONTENT_TYPES,
    ALLOWED_SPREADSHEET_EXTENSIONS,
)


class NewJSONUploadForm(forms.Form):
    file_upload = forms.FileField(
        widget=forms.FileInput(
            attrs={
                "accept": ",".join(ALLOWED_JSON_CONTENT_TYPES + ALLOWED_JSON_EXTENSIONS)
            }
        )
    )


class NewSpreadsheetUploadForm(forms.Form):
    file_upload = forms.FileField(
        widget=forms.FileInput(
            attrs={
                "accept": ",".join(
                    ALLOWED_SPREADSHEET_CONTENT_TYPES + ALLOWED_SPREADSHEET_EXTENSIONS
                )
            }
        )
    )
