from django.apps import AppConfig


class TaskTrackerConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "task_tracker"

    def ready(self):
        import task_tracker.signals  # noqa: F401
