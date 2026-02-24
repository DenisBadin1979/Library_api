from django.urls import path
from rest_framework.permissions import AllowAny
from rest_framework.routers import SimpleRouter, DefaultRouter
from rest_framework_simplejwt.views import (TokenObtainPairView,
                                            TokenRefreshView)

from users.apps import UsersConfig
from users.views import RegisterView, UserViewSet

app_name = UsersConfig.name
router = DefaultRouter()
router.register(r'users', UserViewSet)


urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path(
        "login/",
        TokenObtainPairView.as_view(permission_classes=(AllowAny,)),
        name="login",
    ),
    path(
        "token/refresh/",
        TokenRefreshView.as_view(permission_classes=(AllowAny,)),
        name="token_refresh",
    ),
]

urlpatterns += router.urls