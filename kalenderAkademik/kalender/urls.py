from django.urls import path

from .views import kalender

app_name = 'kalender'

urlpatterns = [
    path('', kalender, name='kaldik'),          # endpoint HTML biasa
]