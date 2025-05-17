from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import KegiatanViewSet

app_name = 'kalender'

router = DefaultRouter()
router.register(r'kegiatan', KegiatanViewSet)

urlpatterns = [
    path('api/', include(router.urls)),         # endpoint REST API
    path('', kalender, name='kaldik'),          # endpoint HTML biasa
]