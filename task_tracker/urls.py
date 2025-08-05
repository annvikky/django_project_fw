from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import EmployeeViewSet, TaskViewSet

app_name = "task_tracker"

router = DefaultRouter()
router.register("employees", EmployeeViewSet)
router.register("tasks", TaskViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
