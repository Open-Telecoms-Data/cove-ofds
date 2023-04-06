from django.conf import settings
from django.conf.urls import url
from django.conf.urls.static import static
from django.urls import re_path

import cove_ofds.views
from libcoveweb2.urls import urlpatterns

handler500 = "libcoveweb2.views.handler500"

urlpatterns += [
    re_path(r"^$", cove_ofds.views.index, name="index"),
    re_path(r"^new_json$", cove_ofds.views.NewJSONInput.as_view(), name="new_json"),
    re_path(r"^new_csvs$", cove_ofds.views.NewCSVInput.as_view(), name="new_csvs"),
    re_path(
        r"^new_spreadsheet$",
        cove_ofds.views.NewSpreadsheetInput.as_view(),
        name="new_spreadsheet",
    ),
    re_path(r"^new_geojson$", cove_ofds.views.new_geojson, name="new_geojson"),
    url(r"^data/(.+)$", cove_ofds.views.ExploreOFDSView.as_view(), name="explore"),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
