from django.contrib import admin

from .models import Employee, Task


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ("full_name", "position", "email", "phone")
    search_fields = ("full_name", "email", "phone")
    list_filter = ("position",)


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("name", "executor", "deadline", "status")
    list_filter = ("status", "deadline")
    search_fields = ("name", "executor__full_name")

    def save_model(self, request, obj, form, change):
        if obj.parent_task_id == 0:
            obj.parent_task = None
        super().save_model(request, obj, form, change)
