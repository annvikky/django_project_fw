from rest_framework import serializers

from .models import Employee, Task


class EmployeeSerializer(serializers.ModelSerializer):
    """Сериализатор для модели сотрудника"""

    class Meta:
        model = Employee
        fields = "__all__"

    def validate_email(self, value):
        """Валидация на корректность Email."""
        value = value.lower()
        allowed_domain = "yourcompany.com"
        domain = value.split("@")[-1]

        if domain != allowed_domain:
            raise serializers.ValidationError(
                f"Email должен быть корпоративным ({allowed_domain})."
            )

        return value

    def validate_phone(self, value):
        """Валидация на корректность ввода тел.номера."""
        if not value.isdigit() or len(value) < 11:
            raise serializers.ValidationError(
                "Номер телефона должен содержать минимум 11 цифр."
            )
        return value


class TaskSerializer(serializers.ModelSerializer):
    """Сериализатор для модели задачи с валидацией и отображением связанных данных."""

    executor_name = serializers.CharField(source="executor.full_name", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Task
        fields = "__all__"
        read_only_fields = ["executor"]

    def to_internal_value(self, data):
        data = data.copy()
        # Преобразуем 0 в None
        if data.get("parent_task") == 0:
            data["parent_task"] = None
        return super().to_internal_value(data)

    def validate(self, data):
        # Проверка: задача не может быть родителем самой себе
        if (
            data.get("parent_task")
            and self.instance
            and data["parent_task"] == self.instance
        ):
            raise serializers.ValidationError(
                "Задача не может быть родителем самой себе."
            )
        return data
