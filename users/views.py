from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.viewsets import ModelViewSet
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from task_tracker.tests import User
from users.serializers import UserLoginSerializer, UserRegistrationSerializer, UserSerializer


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
                schema=UserRegistrationSerializer,
            ),
            status.HTTP_400_BAD_REQUEST: "Ошибки валидации",
        },
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class UserLoginView(TokenObtainPairView):
    serializer_class = (
        UserLoginSerializer  # обычно наследуется от TokenObtainPairSerializer
    )

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
                        "refresh": "jwt_refresh_token",
                    }
                },
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
                "refresh": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Refresh токен"
                ),
            },
            required=["refresh"],
        ),
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Новый access токен",
                examples={"application/json": {"access": "new_jwt_access_token"}},
            ),
            status.HTTP_401_UNAUTHORIZED: "Неверный или просроченный refresh токен",
        },
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)
