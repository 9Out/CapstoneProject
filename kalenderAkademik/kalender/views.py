from django.contrib.auth.models import User
from django.db.models import Q
from django.shortcuts import render
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.views.decorators.csrf import csrf_exempt
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Kategori, Kegiatan, Notifikasi, TahunAkademik
from .serializers import KategoriSerializer, KegiatanSerializer


@api_view(['GET'])
def category_list(request):
    categories = Kategori.objects.all()
    serializer = KategoriSerializer(categories, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@csrf_exempt
def add_kegiatan(request):
    try:
        data = request.data
        nama = data.get('nama')
        deskripsi = data.get('deskripsi', '')
        tgl_mulai = parse_datetime(data.get('start'))
        tgl_selesai = parse_datetime(data.get('end')) if data.get('end') else tgl_mulai
        kategori_id = data.get('kategori_id')
        tahun_akademik_id = data.get('tahun_akademik_id')  
        semester = data.get('semester', 'Ganjil')  

        if not all([nama, tgl_mulai, kategori_id]):
            return Response({'success': False, 'error': 'Nama, tanggal mulai, dan kategori wajib diisi'},
                            status=status.HTTP_400_BAD_REQUEST)

        if tgl_selesai < tgl_mulai:
            return Response({'success': False, 'error': 'Tanggal selesai tidak boleh sebelum tanggal mulai'},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            kategori = Kategori.objects.get(id=kategori_id)
        except Kategori.DoesNotExist:
            return Response({'success': False, 'error': 'Kategori tidak ditemukan'},
                            status=status.HTTP_404_NOT_FOUND)

        tahun_akademik = TahunAkademik.objects.first()
        if tahun_akademik_id:
            try:
                tahun_akademik = TahunAkademik.objects.get(id=tahun_akademik_id)
            except TahunAkademik.DoesNotExist:
                return Response({'success': False, 'error': 'Tahun akademik tidak ditemukan'},
                                status=status.HTTP_404_NOT_FOUND)

        kegiatan = Kegiatan.objects.create(
            tahun_akademik=tahun_akademik,
            semester=semester,
            nama=nama,
            deskripsi=deskripsi,
            tgl_mulai=tgl_mulai,
            tgl_selesai=tgl_selesai,
            user_fk=request.user,
            kategori_fk=kategori
        )

        return Response({'success': True, 'message': 'Kegiatan berhasil ditambahkan'},
                        status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({'success': False, 'error': str(e)},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@csrf_exempt
def save_notification(request):
    try:
        data = request.data
        kegiatan_id = data.get('kegiatan_id')
        metode = data.get('metode')

        if not kegiatan_id or metode not in ['email', 'whatsapp']:
            return Response({'success': False, 'error': 'Kegiatan ID dan metode valid diperlukan'},
                            status=status.HTTP_400_BAD_REQUEST)

        kegiatan = Kegiatan.objects.get(id=kegiatan_id)
        user = request.user

        if not Notifikasi.objects.filter(user_fk=user, kegiatan_fk=kegiatan).exists():
            Notifikasi.objects.create(
                user_fk=user,
                kegiatan_fk=kegiatan,
                metode=metode,
                status='Pending'
            )
            return Response({'success': True, 'message': 'Notifikasi berhasil disimpan'})
        else:
            return Response({'success': False, 'error': 'Notifikasi sudah ada untuk agenda ini'},
                            status=status.HTTP_400_BAD_REQUEST)

    except Kegiatan.DoesNotExist:
        return Response({'success': False, 'error': 'Kegiatan tidak ditemukan'},
                        status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'success': False, 'error': str(e)},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class KegiatanListView(generics.ListAPIView):
    serializer_class = KegiatanSerializer

    def get_queryset(self):
        queryset = Kegiatan.objects.all()
        search = self.request.query_params.get('search')
        start_param = self.request.query_params.get('start')
        end_param = self.request.query_params.get('end')
        year_str = self.request.query_params.get('year')
        month_str = self.request.query_params.get('month')
        academic_year_param = self.request.query_params.get('academic_year')

        if search:
            queryset = queryset.filter(
                Q(nama__icontains=search) | Q(deskripsi__icontains=search)
            ).order_by('tgl_mulai')
        else:
            if start_param and end_param:
                start_date = parse_datetime(start_param)
                end_date = parse_datetime(end_param)
                if start_date and end_date:
                    queryset = queryset.filter(
                        tgl_mulai__lt=end_date,
                        tgl_selesai__gte=start_date
                    ).order_by('tgl_mulai')
            elif academic_year_param:
                queryset = queryset.filter(
                    tahun_akademik__tahun_akademik=academic_year_param
                ).order_by('tgl_mulai')
            else:
                parsed_year = None
                parsed_month = None

                if year_str:
                    try:
                        parsed_year = int(year_str)
                    except ValueError:
                        pass

                if month_str:
                    try:
                        parsed_month = int(month_str)
                        if not (1 <= parsed_month <= 12):
                            parsed_month = None
                    except ValueError:
                        pass

                if parsed_year and parsed_month:
                    queryset = queryset.filter(
                        tgl_mulai__year=parsed_year,
                        tgl_mulai__month=parsed_month
                    ).order_by('tgl_mulai')
                elif parsed_year:
                    queryset = queryset.filter(
                        tgl_mulai__year=parsed_year
                    ).order_by('tgl_mulai')
                elif parsed_month:
                    current_year = timezone.now().year
                    queryset = queryset.filter(
                        tgl_mulai__year=current_year,
                        tgl_mulai__month=parsed_month
                    ).order_by('tgl_mulai')
                else:
                    queryset = queryset.order_by('tgl_mulai')

        return queryset.distinct()


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
@csrf_exempt
def update_kegiatan(request, id):
    try:
        kegiatan = Kegiatan.objects.get(id=id)

        if kegiatan.user_fk != request.user:
            return Response({'success': False, 'error': 'Anda tidak memiliki izin untuk mengedit kegiatan ini'},
                            status=status.HTTP_403_FORBIDDEN)

        data = request.data
        nama = data.get('nama')
        deskripsi = data.get('deskripsi', '')
        tgl_mulai = parse_datetime(data.get('start'))
        tgl_selesai = parse_datetime(data.get('end')) if data.get('end') else tgl_mulai
        kategori_id = data.get('kategori_id')

        if not all([nama, tgl_mulai, kategori_id]):
            return Response({'success': False, 'error': 'Nama, tanggal mulai, dan kategori wajib diisi'},
                            status=status.HTTP_400_BAD_REQUEST)

        if tgl_selesai < tgl_mulai:
            return Response({'success': False, 'error': 'Tanggal selesai tidak boleh sebelum tanggal mulai'},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            kategori = Kategori.objects.get(id=kategori_id)
        except Kategori.DoesNotExist:
            return Response({'success': False, 'error': 'Kategori tidak ditemukan'},
                            status=status.HTTP_404_NOT_FOUND)

        kegiatan.nama = nama
        kegiatan.deskripsi = deskripsi
        kegiatan.tgl_mulai = tgl_mulai
        kegiatan.tgl_selesai = tgl_selesai
        kegiatan.kategori_fk = kategori
        kegiatan.save()

        return Response({'success': True, 'message': 'Kegiatan berhasil diperbarui'},
                        status=status.HTTP_200_OK)

    except Kegiatan.DoesNotExist:
        return Response({'success': False, 'error': 'Kegiatan tidak ditemukan'},
                        status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'success': False, 'error': str(e)},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
@csrf_exempt
def delete_kegiatan(request, id):
    try:
        kegiatan = Kegiatan.objects.get(id=id)

        if kegiatan.user_fk != request.user:
            return Response({'success': False, 'error': 'Anda tidak memiliki izin untuk menghapus kegiatan ini'},
                            status=status.HTTP_403_FORBIDDEN)

        kegiatan.delete()
        return Response({'success': True, 'message': 'Kegiatan berhasil dihapus'},
                        status=status.HTTP_200_OK)

    except Kegiatan.DoesNotExist:
        return Response({'success': False, 'error': 'Kegiatan tidak ditemukan'},
                        status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'success': False, 'error': str(e)},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def kalender(request):
    return render(request, 'kalender/kalenderAkademik.html', {
        'user_id': request.user.id if request.user.is_authenticated else None,
    })