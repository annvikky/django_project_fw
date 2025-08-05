from rest_framework.permissions import BasePermission


class IsAdminOrReadOwn(BasePermission):
    """Разрешает админам — всё, остальным — только свои задачи."""

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.user.is_staff or request.user.is_superuser:
            return True
        return hasattr(obj, "executor") and obj.executor.email == request.user.email
