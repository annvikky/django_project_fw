from django.db.models import Case, Count, IntegerField, Q, Value, When
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from .models import Employee, Task
from .pagination import CustomPagination
from .permissions import IsAdminOrReadOwn
from .serializers import EmployeeSerializer, TaskSerializer


class EmployeeViewSet(viewsets.ModelViewSet):
    """ViewSet для управления сотрудниками (Employee). Включает стандартные CRUD-операции, а также специальный
    эндпоинт `busy` для анализа загруженности сотрудников."""

    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    pagination_class = CustomPagination

    @swagger_auto_schema(
        operation_summary="Получить список сотрудников",
        operation_description="Возвращает список всех сотрудников с поддержкой пагинации.",
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Получить данные сотрудника",
        operation_description="Возвращает детали сотрудника по ID.",
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Создать нового сотрудника",
        operation_description="Создаёт нового сотрудника с указанными данными.",
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Обновить данные сотрудника",
        operation_description="Полностью обновляет данные сотрудника по ID.",
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Частично обновить данные сотрудника",
        operation_description="Обновляет частично поля сотрудника по ID.",
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Удалить сотрудника",
        operation_description="Удаляет сотрудника по ID.",
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    @method_decorator(cache_page(60 * 15))
    @swagger_auto_schema(
        operation_summary="Список сотрудников с количеством активных задач",
        operation_description="Возвращает сотрудников с количеством задач в статусах todo и in_progress, "
        "отсортированных по загруженности.",
    )
    @action(detail=False, methods=["get"])
    def busy(self, request):
        """Возвращает список сотрудников с количеством активных задач (_todo, in_progress), отсортированных по
        загруженности."""

        employees = Employee.objects.annotate(
            active_tasks=Count(
                "tasks", filter=Q(tasks__status__in=["todo", "in_progress"])
            )
        ).order_by("-active_tasks")

        # Пагинация списка сотрудников с активными задачами
        page = self.paginate_queryset(employees)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(employees, many=True)
        return Response(serializer.data)


class TaskViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления задачами. Включает стандартные CRUD-операции.
    Поддержка автоназначения исполнителя и фильтрации доступа.
    """

    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOwn]
    pagination_class = CustomPagination

    @swagger_auto_schema(
        operation_summary="Получить список задач",
        operation_description="Возвращает список задач с учётом прав доступа и пагинацией.",
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Получить данные задачи",
        operation_description="Возвращает детали задачи по ID.",
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Создать новую задачу",
        operation_description="Создаёт новую задачу с автоматическим назначением исполнителя, если возможно.",
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Обновить задачу",
        operation_description="Полностью обновляет данные задачи по ID. При статусе 'done' перераспределяет задачи в "
        "очереди.",
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Частично обновить задачу",
        operation_description="Обновляет частично поля задачи по ID.",
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Удалить задачу",
        operation_description="Удаляет задачу по ID.",
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return Task.objects.all()
        return Task.objects.filter(executor__email=user.email)

    def perform_create(self, serializer):
        """Переопределенное создание задачи с автоназначением исполнителя."""
        task = serializer.save()
        executor = self._assign_executor(task)
        if executor:
            task.status = "in_progress"
            task.queued = False
        else:
            task.queued = True
        task.save()

    def perform_update(self, serializer):
        """Автоматическое перераспределение, если задача завершена."""
        task = serializer.save()
        if task.status == "done":
            self.distribute_queued_tasks()

    def _assign_executor(self, task):
        """Автоматическое назначение исполнителя с ограничением по нагрузке и приоритетом родительского."""
        employees = list(
            Employee.objects.annotate(
                active_tasks=Count("tasks", filter=Q(tasks__status="in_progress"))
            ).order_by("active_tasks")
        )

        if not employees:
            return None

        min_load = employees[0].active_tasks
        load_map = {e.id: e.active_tasks for e in employees}

        # Попытка назначить родительского исполнителя
        if task.parent_task and task.parent_task.executor:
            parent_executor = task.parent_task.executor
            parent_load = load_map.get(parent_executor.id, 0)

            if parent_load <= min_load + 2 and parent_load < 5:
                task.executor = parent_executor
                return parent_executor

        # Назначить самого свободного, если у него < 5 задач
        for employee in employees:
            if load_map[employee.id] < 5:
                task.executor = employee
                return employee

        # Все перегружены — задача в очередь
        return None

    def _get_candidates_for_task(self, task, employees):
        """
        Возвращает подходящего исполнителя для назначения (или None), список ФИО кандидатов для важной задачи
        """
        if not employees:
            return None, []

        min_load = (
            employees[0].active_tasks
            if hasattr(employees[0], "active_tasks")
            else employees[0].task_count
        )

        load_map = {
            e.id: getattr(e, "active_tasks", getattr(e, "task_count", 0))
            for e in employees
        }

        candidates = set()

        # Родительский исполнитель
        parent_executor = None
        if task.executor:
            parent_executor = task.executor
        elif task.parent_task and task.parent_task.executor:
            parent_executor = task.parent_task.executor

        assigned_executor = None

        if parent_executor:
            parent_load = load_map.get(parent_executor.id, 0)
            if parent_load <= min_load + 2 and parent_load < 5:
                candidates.add(parent_executor.full_name)
                assigned_executor = parent_executor

        # Добавляем наименее загруженных сотрудников (нагрузка < 5)
        for e in employees:
            if load_map.get(e.id, 0) < 5:
                candidates.add(e.full_name)

        return assigned_executor, list(candidates)

    def distribute_queued_tasks(self):
        """Автоматическое распределение задач из очереди с учётом приоритета родительской задачи и лимита в 5 задач."""
        queued_tasks = (
            Task.objects.filter(queued=True)
            .annotate(
                has_parent=Case(
                    When(parent_task__isnull=False, then=Value(0)),
                    default=Value(1),
                    output_field=IntegerField(),
                )
            )
            .order_by("has_parent", "created_at")
        )

        # Получаем сотрудников с количеством задач в работе
        employees = list(
            Employee.objects.annotate(
                active_tasks=Count("tasks", filter=Q(tasks__status="in_progress"))
            ).order_by("active_tasks")
        )

        if not employees:
            return

        load = {e.id: e.active_tasks for e in employees}

        for task in queued_tasks:
            assigned_executor, _ = self._get_candidates_for_task(task, employees)

            if assigned_executor and load.get(assigned_executor.id, 0) < 5:
                task.executor = assigned_executor
                task.status = "in_progress"
                task.queued = False
                task.save()

                load[assigned_executor.id] = load.get(assigned_executor.id, 0) + 1
            else:
                # Назначаем наименее загруженного сотрудника с нагрузкой < 5
                assigned = False
                for employee in employees:
                    if load.get(employee.id, 0) < 5:
                        task.executor = employee
                        task.status = "in_progress"
                        task.queued = False
                        task.save()

                        load[employee.id] = load.get(employee.id, 0) + 1
                        assigned = True
                        break

                if not assigned:
                    task.queued = True
                    task.save()

    @method_decorator(cache_page(60 * 15))
    @action(detail=False, methods=["get"])
    def in_progress_tasks(self, request):
        # Получаем задачи со статусом in_progress
        tasks = (
            Task.objects.filter(status="in_progress")
            .select_related("executor")
            .order_by("deadline")
        )

        page = self.paginate_queryset(tasks)
        if page is not None:
            data = [
                {
                    "Важная задача": task.name,
                    "Срок": task.deadline,
                    "Исполнитель": [task.executor.full_name] if task.executor else [],
                }
                for task in page
            ]
            return self.get_paginated_response(data)

        data = [
            {
                "Важная задача": task.name,
                "Срок": task.deadline,
                "Исполнитель": [task.executor.full_name] if task.executor else [],
            }
            for task in tasks
        ]
        return Response(data)

    @method_decorator(cache_page(60 * 15))
    @action(detail=False, methods=["get"])
    def important(self, request):
        """Задачи в статусе _todo, от которых зависят задачи в работе."""
        parent_ids = (
            Task.objects.filter(status="in_progress")
            .exclude(parent_task__isnull=True)
            .values_list("parent_task", flat=True)
            .distinct()
        )

        important_tasks = Task.objects.filter(
            id__in=parent_ids, status="todo"
        ).order_by("deadline")

        # Получаем сотрудников с нагрузкой
        employees = list(
            Employee.objects.annotate(
                task_count=Count("tasks", filter=Q(tasks__status="in_progress"))
            ).order_by("task_count")
        )

        if not employees:
            return Response([])

        page = self.paginate_queryset(important_tasks)
        if page is not None:
            result = []
            for task in page:
                _, candidates = self._get_candidates_for_task(task, employees)
                result.append(
                    {
                        "Важная задача": task.name,
                        "Срок": task.deadline,
                        "Кандидаты": candidates,
                    }
                )
            return self.get_paginated_response(result)

        result = []
        for task in important_tasks:
            _, candidates = self._get_candidates_for_task(task, employees)
            result.append(
                {
                    "Важная задача": task.name,
                    "Срок": task.deadline,
                    "Кандидаты": candidates,
                }
            )
        return Response(result)

    @method_decorator(cache_page(60 * 15))
    @action(detail=False, methods=["get"])
    def queued(self, request):
        """Возвращает задачи в очереди, отсортированные по сроку. Поддерживает фильтрацию по родительской задаче."""
        parent_id = request.query_params.get("parent_task")

        tasks = Task.objects.filter(queued=True)
        if parent_id:
            tasks = tasks.filter(parent_task_id=parent_id)

        tasks = tasks.order_by("deadline")

        # Пагинация списка задач в очереди
        page = self.paginate_queryset(tasks)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(tasks, many=True)

        return Response(serializer.data)
