from django.core.mail import send_mail
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Task
from .views import TaskViewSet


@receiver(post_save, sender=Task)
def notify_employee_by_email(sender, instance, created, **kwargs):
    """
    Отправляет email-уведомление назначенному исполнителю задачи,
    если установлен флаг notify_email.
    """
    if created and instance.notify_email:
        executor = instance.executor
        if executor and executor.email:
            send_mail(
                subject=f"Новое задание: {instance.name}",
                message=(
                    f"Здравствуйте, {executor.full_name}!\n\n"
                    f"Вам назначено новое задание:\n\n"
                    f"{instance.name}\n"
                    f"Срок: {instance.deadline}\n\n"
                    f"Пожалуйста, перейдите в систему для получения подробностей."
                ),
                from_email="noreply@example.com",
                recipient_list=[executor.email],
                fail_silently=False,
            )


@receiver(post_save, sender=Task)
def auto_distribute_queued_tasks(sender, instance, **kwargs):
    # Если задача в очереди, запускаем распределение
    if instance.queued:
        TaskViewSet().distribute_queued_tasks()
