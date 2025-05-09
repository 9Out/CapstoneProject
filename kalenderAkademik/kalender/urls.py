from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views
from .views import KegiatanViewSet

app_name = 'kalender'
urlpatterns = [
    path('', views.kalender, name='kaldik'),
]

router = DefaultRouter()
router.register(r'kegiatan', KegiatanViewSet)

urlpatterns = [
    path('', include(router.urls)),
]