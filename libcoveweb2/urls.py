from django.contrib import admin
from django.urls import include, re_path
from django.views.generic import TemplateView

urlpatterns = [
    re_path(
        r"^terms/$",
        TemplateView.as_view(template_name="libcoveweb2/terms.html"),
        name="terms",
    ),
    re_path(r"^admin/", admin.site.urls),
    re_path(r"^i18n/", include("django.conf.urls.i18n")),
]
