from django.shortcuts import render
from rest_framework import viewsets

from .models import Kegiatan
from .serializer import KegiatanSerializer


class KegiatanViewSet(viewsets.ModelViewSet):
    queryset = Kegiatan.objects.all()
    serializer_class = KegiatanSerializer

# Create your views here.
def kalender(request):
    return render(request, 'kalender/kaldik.html')