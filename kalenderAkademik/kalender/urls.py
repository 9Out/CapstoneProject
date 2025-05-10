from django.urls import include, path
from rest_framework.routers import DefaultRouter
from . import views
# from .views import KegiatanViewSet
from .views import KegiatanListView, save_notification


app_name = 'kalender'

# router = DefaultRouter()
# router.register(r'kegiatan', KegiatanViewSet)

urlpatterns = [
    path('', views.kalender, name='kaldik'),
    # path('kegiatan/', include(router.urls)),
    path('events/', KegiatanListView.as_view(), name='kegiatan-list'),
    path('save-notification/', save_notification, name='save-notification'),
]


