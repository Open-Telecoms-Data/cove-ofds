from django.conf import settings
from django.conf.urls import url
from django.conf.urls.static import static
from django.urls import re_path

import cove_ofds.views
from libcoveweb2.urls import urlpatterns

urlpatterns += [
    re_path(r"^$", cove_ofds.views.index, name="index"),
    url(r"^data/(.+)$", cove_ofds.views.explore_ofds, name="explore"),
    re_path(r"^new_geojson$", cove_ofds.views.new_geojson, name="new_geojson"),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
