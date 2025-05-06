from django.urls import path
from . import views


app_name = 'kalender'
urlpatterns = [
    path('', views.kalender, name='kaldik'),
]