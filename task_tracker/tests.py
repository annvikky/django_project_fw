from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils.timezone import now
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from task_tracker.models import Employee, Task

User = get_user_model()


class CRUDTestCase(APITestCase):
    """Тесты на CRUD модели для суперпользователя."""

    def setUp(self):
        # Создаем суперпользователя (админ для доступа к EmployeeViewSet)
        self.admin = User.objects.create_superuser(
            username="admin", email="admin@test.com", password="adminpass"
        )
        # Получаем токен авторизации
        refresh = RefreshToken.for_user(self.admin)
        access_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

        # Данные для сотрудника
        self.employee_data = {
            "full_name": "Иван Иванов",
            "position": "Разработчик",
            "email": "ivanov@yourcompany.com",
            "phone": "89991112233",
        }

        # Создаем сотрудника
        response = self.client.post(
            reverse("task_tracker:employee-list"), self.employee_data
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.employee = Employee.objects.get(email=self.employee_data["email"])

        # Данные для задачи
        self.task_data = {
            "name": "Тестовая задача",
            "description": "Описание",
            "executor": self.employee.id,
            "deadline": (date.today() + timedelta(days=7)).isoformat(),
            "status": "todo",
            "queued": False,
            "comment": "Комментарий",
        }

    def test_employee_crud(self):
        # Create проверен в setUp

        # Read
        response = self.client.get(
            reverse("task_tracker:employee-detail", args=[self.employee.id])
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["full_name"], self.employee_data["full_name"])

        # Update
        updated_data = {**self.employee_data, "position": "Team Lead"}
        response = self.client.put(
            reverse("task_tracker:employee-detail", args=[self.employee.id]),
            updated_data,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["position"], "Team Lead")

        # Delete
        response = self.client.delete(
            reverse("task_tracker:employee-detail", args=[self.employee.id])
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Employee.objects.filter(id=self.employee.id).exists())

    def test_task_crud(self):
        # Create
        response = self.client.post(reverse("task_tracker:task-list"), self.task_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        task_id = response.data["id"]

        # Read
        response = self.client.get(reverse("task_tracker:task-detail", args=[task_id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], self.task_data["name"])

        # Update
        updated_data = {**self.task_data, "status": "in_progress"}
        response = self.client.put(
            reverse("task_tracker:task-detail", args=[task_id]), updated_data
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "in_progress")

        # Delete
        response = self.client.delete(
            reverse("task_tracker:task-detail", args=[task_id])
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Task.objects.filter(id=task_id).exists())


class InProgressTasksTest(APITestCase):
    def setUp(self):
        # Создаем пользователя и аутентифицируемся (если требуется)
        self.user = User.objects.create_user(username="testuser2", password="testpass2")
        # Генерируем JWT токен
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)
        # Создаем клиент и передаем токен
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")
        # Создаем employee
        self.employee = Employee.objects.create(
            full_name="Петров",
            email="petrov@yourcompany.com",
            position="Бухгалтер",
            phone="+79992223344",
        )

        # Создаем 11 задач со статусом 'in_progress'
        for i in range(11):
            Task.objects.create(
                name=f"Task {i}",
                status="in_progress",
                executor=self.employee,
                deadline=now().date() + timedelta(days=i),
            )

    def test_in_progress_tasks_paginated(self):
        """Тест на пагинацию и фильтрацию задач со статусом 'in_progress'."""
        url = reverse("task_tracker:task-in-progress-tasks")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertLessEqual(len(response.data["results"]), 10)


class QueuedTasksTest(APITestCase):
    def setUp(self):
        # Создаем пользователя и аутентифицируемся
        self.user = User.objects.create_user(username="testuser4", password="testpass4")
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

        # Создаем сотрудника
        self.employee = Employee.objects.create(
            full_name="Иванов Иван",
            position="Разработчик",
            email="ivanov@yourcompany.com",
            phone="+79991112233",
        )

    def test_queued_tasks_filtered_by_parent(self):
        """Тест queued с фильтрацией по родительской задаче."""
        parent = Task.objects.create(
            name="Parent", status="todo", queued=True, deadline=date.today()
        )
        Task.objects.create(
            name="Child Queued",
            status="todo",
            queued=True,
            parent_task=parent,
            deadline=date.today(),
        )

        # Задача, не связанная с parent
        Task.objects.create(
            name="Unrelated", status="todo", queued=True, deadline=date.today()
        )

        url = reverse("task_tracker:task-queued") + f"?parent_task={parent.id}"
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertIn("results", response.data)

        # Проверяем, что вернулись только задачи с нужным parent_task
        for task in response.data["results"]:
            self.assertEqual(task["parent_task"], parent.id)


class EmployeeBusyTest(APITestCase):
    def setUp(self):
        # Создаем пользователя и аутентифицируемся
        self.user = User.objects.create_user(
            username="testuser5",
            password="testpass5",
            email="testuser5@yourcompany.com",
            is_staff=True,
            is_superuser=True,
        )
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

        # Создаем сотрудника, связанного с self.user
        self.employee = Employee.objects.create(
            full_name="Иванов",
            email="ivanov@yourcompany.com",
            position="Программист",
            phone="+79991112233",
        )

    def test_busy_action_returns_sorted_employees(self):
        """Тест busy с возвратом списка сотрудников."""
        User.objects.create_user(
            username="user5", password="12345", email="user5@yourcompany.com"
        )
        emp2 = Employee.objects.create(
            full_name="Петров",
            email="petrov@yourcompany.com",
            position="Бухгалтер",
            phone="+79992223344",
        )

        # Создаем задачи
        Task.objects.create(
            name="T1",
            status="in_progress",
            executor=self.employee,
            deadline=date.today(),
        )
        Task.objects.create(
            name="T2", status="todo", executor=emp2, deadline=date.today()
        )

        url = reverse("task_tracker:employee-busy")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertIn("results", response.data)
        self.assertTrue(len(response.data["results"]) >= 1)
