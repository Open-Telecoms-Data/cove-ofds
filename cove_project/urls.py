from django.conf import settings
from django.conf.urls import url
from django.conf.urls.static import static

import cove_ofds.views
from libcoveweb2.urls import urlpatterns

urlpatterns += [url(r"^data/(.+)$", cove_ofds.views.explore_ofds, name="explore")]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
