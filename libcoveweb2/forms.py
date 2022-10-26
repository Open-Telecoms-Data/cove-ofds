from django import forms


class NewJSONUploadForm(forms.Form):
    file_upload = forms.FileField()
