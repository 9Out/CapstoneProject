from django.shortcuts import render
from rest_framework import generics
from .serializers import KegiatanSerializer
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.views.decorators.csrf import csrf_exempt
from .models import Notifikasi, Kegiatan
from django.contrib.auth.models import User
from django.utils.dateparse import parse_datetime

# Create your views here.
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@csrf_exempt
def save_notification(request):
    try:
        data = request.data
        kegiatan_id = data.get('kegiatan_id')
        metode = data.get('metode')

        if not kegiatan_id or metode not in ['email', 'whatsapp']:
            return Response({'success': False, 'error': 'Kegiatan ID dan metode valid diperlukan'}, status=status.HTTP_400_BAD_REQUEST)

        kegiatan = Kegiatan.objects.get(id=kegiatan_id)
        user = request.user  # Ambil user yang login

        # Cek apakah notifikasi sudah ada untuk user dan kegiatan ini
        if not Notifikasi.objects.filter(user_fk=user, kegiatan_fk=kegiatan).exists():
            Notifikasi.objects.create(
                user_fk=user,
                kegiatan_fk=kegiatan,
                metode=metode,
                status='Pending'
            )
            return Response({'success': True, 'message': 'Notifikasi berhasil disimpan'})
        else:
            return Response({'success': False, 'error': 'Notifikasi sudah ada untuk agenda ini'}, status=status.HTTP_400_BAD_REQUEST)

    except Kegiatan.DoesNotExist:
        return Response({'success': False, 'error': 'Kegiatan tidak ditemukan'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class KegiatanListView(generics.ListAPIView):
    queryset = Kegiatan.objects.all()
    serializer_class = KegiatanSerializer
    def get_queryset(self):
        queryset = Kegiatan.objects.all()
        start = self.request.query_params.get('start')
        end = self.request.query_params.get('end')

        if start and end:
            start_date = parse_datetime(start)
            end_date = parse_datetime(end)
            if start_date and end_date:
                queryset = queryset.filter(
                    tgl_mulai__gte=start_date,
                    tgl_selesai__lte=end_date
                ).order_by('tgl_mulai')
        return queryset



def kalender(request):
    return render(request, 'kalender/kalenderAkademik.html')

