from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Task
from .tasks import send_task_email
from .views import TaskViewSet


@receiver(post_save, sender=Task)
def notify_employee_by_email(sender, instance, created, **kwargs):
    """
    Отправляет email-уведомление назначенному исполнителю задачи
    через Celery, если установлен флаг notify_email.
    """

    if instance.notify_email and instance.executor and instance.executor.email:
        # print("Sending email via Celery!")  # для отладки
        send_task_email.delay(
            instance.executor.full_name,
            instance.name,
            str(instance.deadline),
            instance.executor.email,
        )

        # Автораспределение
    if instance.queued:
        TaskViewSet().distribute_queued_tasks()
