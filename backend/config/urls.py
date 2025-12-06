from django.contrib import admin
from django.urls import path, include
from frontend import views as frontend_views   # 홈 연결을 위해 필요
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # 프론트엔드 페이지 라우팅
    path('', include('frontend.urls')),

    # API 엔드포인트는 모두 /api/ 아래에 위치
    path('', include('recipes.urls')),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)