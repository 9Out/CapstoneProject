from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views
from .views import KegiatanViewSet

app_name = 'kalender'

router = DefaultRouter()
router.register(r'kegiatan', KegiatanViewSet)

urlpatterns = [
    path('', views.kalender, name='kaldik'),
    path('api/', include(router.urls)),
]