from rest_framework.generics import CreateAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.viewsets import ModelViewSet
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from task_tracker.tests import User
from users.serializers import UserRegistrationSerializer, UserLoginSerializer, UserSerializer


class UserViewSet(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_permissions(self):
        if self.action in ["create"]:
            return [AllowAny()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        user = serializer.save(is_active=True)
        user.set_password(user.password)
        user.save()

    @swagger_auto_schema(operation_description="Получить список пользователей")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Создать нового пользователя (регистрация)"
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(operation_description="Получить пользователя по ID")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(operation_description="Обновить данные пользователя")
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(operation_description="Частичное обновление пользователя")
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(operation_description="Удалить пользователя")
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


class RegisterView(CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_summary="Регистрация нового пользователя",
        operation_description="Создаёт нового пользователя с передачей данных регистрации.",
        responses={
            status.HTTP_201_CREATED: openapi.Response(
                description="Пользователь успешно создан",
                schema=UserRegistrationSerializer()
            ),
            status.HTTP_400_BAD_REQUEST: "Ошибки валидации",
        },
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class UserLoginView(TokenObtainPairView):
    serializer_class = UserLoginSerializer  # обычно наследуется от TokenObtainPairSerializer

    @swagger_auto_schema(
        operation_summary="Аутентификация пользователя (логин)",
        operation_description="Получение JWT access и refresh токенов при успешном логине.",
        request_body=UserLoginSerializer,
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Токены успешно получены",
                examples={
                    "application/json": {
                        "access": "jwt_access_token",
                        "refresh": "jwt_refresh_token"
                    }
                }
            ),
            status.HTTP_401_UNAUTHORIZED: "Неверные учётные данные",
        },
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class TokenRefreshViewCustom(TokenRefreshView):

    @swagger_auto_schema(
        operation_summary="Обновление access токена",
        operation_description="Обновление JWT access токена по refresh токену.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "refresh": openapi.Schema(type=openapi.TYPE_STRING, description="Refresh токен"),
            },
            required=["refresh"],
        ),
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Новый access токен",
                examples={
                    "application/json": {
                        "access": "new_jwt_access_token"
                    }
                }
            ),
            status.HTTP_401_UNAUTHORIZED: "Неверный или просроченный refresh токен",
        },
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)
