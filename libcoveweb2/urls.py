from django.contrib import admin
from django.urls import include, re_path
from django.views.generic import TemplateView

import libcoveweb2.views

urlpatterns = [
    re_path(r"^$", libcoveweb2.views.index, name="index"),
    re_path(r"^new_json$", libcoveweb2.views.new_json, name="new_json"),
    re_path(
        r"^new_spreadsheet$", libcoveweb2.views.new_spreadsheet, name="new_spreadsheet"
    ),
    # TODO move terms.html template into libcoveweb2
    re_path(
        r"^terms/$", TemplateView.as_view(template_name="terms.html"), name="terms"
    ),
    re_path(r"^admin/", admin.site.urls),
    re_path(r"^i18n/", include("django.conf.urls.i18n")),
]
