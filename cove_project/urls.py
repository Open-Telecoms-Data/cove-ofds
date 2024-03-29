import libcoveweb2.views
from django.conf import settings
from django.conf.urls.static import static
from django.urls import re_path
from libcoveweb2.urls import urlpatterns

import cove_ofds.views

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
    re_path(
        r"^data/([\w\-]+)$", cove_ofds.views.ExploreOFDSView.as_view(), name="explore"
    ),
    re_path(
        r"^data/([\w\-]+)/processing_status_api$",
        libcoveweb2.views.ExploreDataProcessingStatusAPIView.as_view(),
        name="explore_processing_status_api$",
    ),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
