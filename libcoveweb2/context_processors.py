from django.conf import settings


def from_settings(request):
    context = {
        "input_methods": settings.COVE_CONFIG.get("input_methods", []),
        "app_verbose_name": settings.COVE_CONFIG.get("app_verbose_name", []),
        "piwik": getattr(settings, "PIWIK", {"dimension_map": {}}),
        "google_analytics_id": getattr(settings, "GOOGLE_ANALYTICS_ID", ""),
        "sentry_dsn": getattr(settings, "SENTRY_DSN", ""),
        "delete_files_after_days": getattr(settings, "DELETE_FILES_AFTER_DAYS", 7),
    }
    return context
