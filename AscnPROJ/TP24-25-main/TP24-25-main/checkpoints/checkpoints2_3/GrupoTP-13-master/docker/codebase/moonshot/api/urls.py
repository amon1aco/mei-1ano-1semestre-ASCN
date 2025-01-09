from django.urls import path, re_path, include
from rest_framework import permissions
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView
from rest_framework.routers import DefaultRouter
from .views import (
    DigitalGreenCertificateVerificationViewSet,
    HealthViewSet,
    VaccinationViewSet,
    RecoveryViewSet,
    TestViewSet,
    NotifierViewSet,
    DigitalGreenCertificateViewSet,
    ObtainJWTPairView,
)
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="Moonshot API",
        default_version="v1",
        description="Documentation for the Moonshot API",
        contact=openapi.Contact(email="moonshot@gmail.com"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

router = DefaultRouter()
router.register("vaccinations", VaccinationViewSet, basename="vaccinations")
router.register("recoveries", RecoveryViewSet, basename="recoveries")
router.register("tests", TestViewSet, basename="tests")
router.register("notifiers", NotifierViewSet, basename="notifiers")
router.register("certificates", DigitalGreenCertificateViewSet, basename="certificates")

urlpatterns = [
    re_path(
        r"^swagger(?P<format>\.json|\.yaml)$",
        schema_view.without_ui(cache_timeout=0),
        name="schema-json",
    ),
    re_path(
        r"^swagger/$",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
    re_path(
        r"^redoc/$", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"
    ),
    re_path(r"^auth/login/", ObtainJWTPairView.as_view(), name="token_obtain_pair"),
    re_path(r"^auth/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    re_path(r"^auth/verify/", TokenVerifyView.as_view(), name="token_verify"),
    path("", include(router.urls)),
    path("", include([path("health", HealthViewSet.as_view())])),
    path(
        "",
        include(
            [
                path(
                    "certificates/verify",
                    DigitalGreenCertificateVerificationViewSet.as_view(),
                )
            ]
        ),
    ),
]
