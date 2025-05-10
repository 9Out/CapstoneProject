from django.shortcuts import render
from rest_framework import viewsets

from .models import Kegiatan
from .serializer import KegiatanSerializer


class KegiatanViewSet(viewsets.ModelViewSet):
    queryset = Kegiatan.objects.all()
    serializer_class = KegiatanSerializer

def kalender(request):
    return render(request, 'kalender/kaldik.html')