from django.db import models


class Employee(models.Model):
    full_name = models.CharField(
        max_length=255, verbose_name="ФИО", help_text="Введите ФИО сотрудника"
    )
    position = models.CharField(
        max_length=100, verbose_name="Должность", help_text="Укажите должность"
    )

    email = models.EmailField(
        unique=True, verbose_name="Email", help_text="Укажите почту"
    )
    phone = models.CharField(
        max_length=15, verbose_name="Телефон", help_text="Введите номер телефона"
    )

    def __str__(self):
        return self.full_name


class Task(models.Model):
    STATUS_CHOICES = [
        ("todo", "Ожидает начала"),
        ("in_progress", "В работе"),
        ("done", "Выполнена"),
    ]

    name = models.CharField(
        max_length=255, verbose_name="Задача", help_text="Поставьте задачу"
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name="Описание задачи",
        help_text="Опишите задачу подробнее (если требуется)",
    )
    parent_task = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="subtasks",
        verbose_name="Родительская задача",
        help_text="Укажите ID родительской задачи, если она есть, по умолчанию отсутствует",
    )
    executor = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="tasks",
        verbose_name="Исполнитель",
        help_text="Подбор сотрудника-исполнителя",
    )
    deadline = models.DateField(
        verbose_name="Срок выполнения", help_text="Укажите дату в формате YYYY:mm:dd"
    )
    queued = models.BooleanField(default=False, verbose_name="Очередь назначения")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="todo",
        verbose_name="Статус",
        help_text="Отражение статуса выполнения",
    )
    comment = models.TextField(
        blank=True, verbose_name="Комментарий", help_text="Укажите доп.информацию"
    )
    attachment = models.FileField(
        upload_to="attachments/",
        null=True,
        blank=True,
        verbose_name="Вложение",
        help_text="Прикрепите файл при необходимости",
    )
    notify_email = models.BooleanField(default=True, verbose_name="Оповещение по Email")

    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.executor is None:
            self.queued = True
            self.status = "todo"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
