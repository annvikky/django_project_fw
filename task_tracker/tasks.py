from celery import shared_task
from django.core.mail import send_mail


@shared_task
def send_task_email(full_name, task_name, deadline, email):
    subject = f"Новое задание: {task_name}"
    message = (
        f"Здравствуйте, {full_name}!\n\n"
        f"Вам назначено новое задание:\n\n"
        f"{task_name}\n"
        f"Срок: {deadline}\n\n"
        f"Пожалуйста, перейдите в систему для получения подробностей."
    )
    send_mail(
        subject=subject,
        message=message,
        from_email="noreply@example.com",
        recipient_list=[email],
        fail_silently=False,
    )
