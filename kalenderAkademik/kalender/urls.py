from django.urls import include, path
from . import views


app_name = 'kalenderPage'
urlpatterns = [
    path('', views.kalender, name='kaldik'),
]


