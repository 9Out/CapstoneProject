from django.urls import include, path
from . import views

# Pilih salah satu nama app yang sesuai kebutuhan
app_name = 'kalender'  # atau 'kalenderPage', sesuaikan dengan views dan struktur project

urlpatterns = [
    path('', views.kalender, name='kaldik'),
]
