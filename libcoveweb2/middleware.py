from django.conf import settings
from django.utils.deprecation import MiddlewareMixin


class CoveConfigCurrentApp(MiddlewareMixin):
    def process_view(self, request, view_func, view_args, view_kwargs):
        request.current_app = settings.COVE_CONFIG["app_name"]
        request.current_app_base_template = settings.COVE_CONFIG["app_base_template"]
