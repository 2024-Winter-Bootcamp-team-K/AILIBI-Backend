"""
URL configuration for Backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, re_path, include
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.conf.urls.static import static

schema_view = get_schema_view(
    openapi.Info(
        title="Team-K AILIBI",
        default_version='ver.1',
        description="Team-K AILIBI API 문서",
        terms_of_service="https://www.google.com/policies/terms/",
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
    url='https://www.ailibi.click/api/v1/',
)

urlpatterns = [
    path(r'swagger(?P<format>\.json|\.yaml)', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path(r'swagger', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path(r'redoc', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc-v1'),
    path('metrics', csrf_exempt(include('django_prometheus.urls'))),
    path("admin/", admin.site.urls),
    path("health", include("health.urls")),
    path('api/v1/stt', include('stt.urls')),
    path('api/v1/auth', include('user.urls')),  # 사용자 로그인/회원가입

    #path('users/', include('user.users_urls')),  # 사용자 정보 불러오기
    path('api/v1/scenarios', include('llm.urls')), # 시나리오 생성

    path('api/v1/histories', include('scenario.urls')),  # /histories?user_id={userId}, /histories?scenario_id={scenarioId}, /histories?suspect_id={suspectId}, /histories?scenario_id={scenarioId}
    path('api/v1/scenarios/<int:scenario_id>', include('scenario.scenario_urls')), # /scenarios/{scenario_id}, /scenarios/{scenario_id}

    path('api/v1/suspects', include('suspect.urls')), # /suspects?scenario_id={scenarioId}

    path('api/v1/suspects/<int:suspect_id>', include('suspect.suspect_urls')), # /suspects/{suspect_id}

    path('api/v1/evidences', include('evidence.urls')), # /evidences?scenario_id={scenarioId}, /evidences/{evidence_id}

    path('api/v1/tts', include('tts.urls')),

    path('api/v1/chat', include('chat.urls')),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)