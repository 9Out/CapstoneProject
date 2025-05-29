from django.shortcuts import render
from rest_framework import generics
from .serializers import KegiatanSerializer, KategoriSerializer
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from .models import Notifikasi, Kegiatan, Kategori, TahunAkademik
# from django.contrib.auth.models import User
from .tasks import send_email_notification, send_whatsapp_notification
from django.utils.dateparse import parse_datetime
from django.utils import timezone
from django.contrib.auth import get_user_model

# Create your views here.


@api_view(['GET'])
def category_list(request):
    categories = Kategori.objects.all()
    serializer = KategoriSerializer(categories, many=True)
    return Response(serializer.data)

@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_kegiatan(request):
    try:
        data = request.data
        nama = data.get('nama')
        deskripsi = data.get('deskripsi', '')
        tgl_mulai = parse_datetime(data.get('start'))
        tgl_selesai = parse_datetime(data.get('end')) if data.get('end') else tgl_mulai.replace(hour=23, minute=59, second=59)
        kategori_id = data.get('kategori_id')
        tahun_akademik_id = data.get('tahun_akademik_id')   
        semester = data.get('semester', 'Ganjil')  

        # Validasi input
        if not all([nama, tgl_mulai, kategori_id]):
            return Response(
                {'success': False, 'error': 'Nama, tanggal mulai, dan kategori wajib diisi'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if tgl_selesai < tgl_mulai:
            return Response(
                {'success': False, 'error': 'Tanggal selesai tidak boleh sebelum tanggal mulai'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            kategori = Kategori.objects.get(id=kategori_id)
        except Kategori.DoesNotExist:
            return Response(
                {'success': False, 'error': 'Kategori tidak ditemukan'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Tentukan tahun akademik
        tahun_akademik = TahunAkademik.objects.first()   
        if tahun_akademik_id:
            try:
                tahun_akademik = TahunAkademik.objects.get(id=tahun_akademik_id)
            except TahunAkademik.DoesNotExist:
                return Response(
                    {'success': False, 'error': 'Tahun akademik tidak ditemukan'},
                    status=status.HTTP_404_NOT_FOUND
                )

        # Buat kegiatan baru
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
        User = get_user_model()
        users = User.objects.all()

        # Buat notifikasi untuk semua user
        for user in users:
            notifikasi = Notifikasi.objects.create(
                user_fk=user,
                kegiatan_fk=kegiatan,
                metode='email',   
                status='Pending'
            )
            send_email_notification.delay(notifikasi.id)

        return Response(
            {'success': True, 'message': 'Kegiatan berhasil ditambahkan'},
            status=status.HTTP_201_CREATED
        )

    except Exception as e:
        return Response(
            {'success': False, 'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@csrf_exempt
def save_notification(request):
    try:
        data = request.data
        kegiatan_id = data.get('kegiatan_id')
        metode = data.get('metode')
        one_day_before = data.get('one_day_before', False)
        one_hour_before = data.get('one_hour_before', False)

        if not kegiatan_id or metode not in ['email', 'whatsapp']:
            return Response({'success': False, 'error': 'Kegiatan ID dan metode valid diperlukan'}, status=status.HTTP_400_BAD_REQUEST)

        kegiatan = Kegiatan.objects.get(id=kegiatan_id)
        user = request.user  # Ambil user yang login

        # Cek apakah notifikasi sudah ada untuk user dan kegiatan ini dengan metode yang sama
        existing_notification = Notifikasi.objects.filter(
            user_fk=user,
            kegiatan_fk=kegiatan,
            metode=metode
        ).first()

        if existing_notification:
            return Response({'success': False, 'error': f'Notifikasi dengan metode {metode} sudah ada untuk agenda ini'}, status=status.HTTP_400_BAD_REQUEST)

        # Jika tidak ada notifikasi dengan metode yang sama, buat notifikasi baru
        Notifikasi.objects.create(
            user_fk=user,
            kegiatan_fk=kegiatan,
            metode=metode,
            status='Pending',
            one_day_before=one_day_before,
            one_hour_before=one_hour_before
        )

        return Response({'success': True, 'message': f'Notifikasi dengan metode {metode} berhasil disimpan'})

    except Kegiatan.DoesNotExist:
        return Response({'success': False, 'error': 'Kegiatan tidak ditemukan'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class KegiatanListView(generics.ListAPIView):
    serializer_class = KegiatanSerializer

    def get_queryset(self):
        queryset = Kegiatan.objects.filter(is_deleted=False)
        search = self.request.query_params.get('search')
        start_param = self.request.query_params.get('start') 
        end_param = self.request.query_params.get('end')     
        year_str = self.request.query_params.get('year')
        month_str = self.request.query_params.get('month')
        academic_year_param = self.request.query_params.get('academic_year') 

        if search:
            # Jika ada parameter search, cari kegiatan berdasarkan nama atau deskripsi
            queryset = queryset.filter(
                Q(nama__icontains=search) | Q(deskripsi__icontains=search)
            ).order_by('tgl_mulai')
        else:
            # Jika tidak ada search, filter berdasarkan parameter lain
            if start_param and end_param:
                start_date = parse_datetime(start_param)
                end_date = parse_datetime(end_param)
                if start_date and end_date:
                    # Filter untuk kegiatan yang bersinggungan dengan rentang tanggal
                    # Kegiatan yang dimulai sebelum end_date DAN berakhir setelah start_date
                    queryset = queryset.filter(
                        tgl_mulai__lt=end_date,  # Kegiatan dimulai sebelum akhir rentang view
                        tgl_selesai__gte=start_date # Kegiatan berakhir pada atau setelah awal rentang view
                    ).order_by('tgl_mulai')
            elif academic_year_param: # Menggunakan nama variabel yang sudah diubah
                queryset = queryset.filter(tahun_akademik__tahun_akademik=academic_year_param).order_by('tgl_mulai')
            else:
                # Logika untuk filter berdasarkan tahun dan/atau bulan jika start/end tidak ada
                parsed_year = None
                parsed_month = None

                if year_str:
                    try:
                        parsed_year = int(year_str)
                    except ValueError:
                        pass  # parsed_year tetap None jika konversi gagal
                
                if month_str:
                    try:
                        parsed_month = int(month_str)
                        if not (1 <= parsed_month <= 12): # Validasi rentang bulan
                            parsed_month = None 
                    except ValueError:
                        pass  # parsed_month tetap None jika konversi gagal

                if parsed_year and parsed_month:
                    # Filter berdasarkan tahun dan bulan spesifik
                    queryset = queryset.filter(
                        tgl_mulai__year=parsed_year,
                        tgl_mulai__month=parsed_month
                    ).order_by('tgl_mulai')
                elif parsed_year:
                    # Filter hanya berdasarkan tahun spesifik
                    queryset = queryset.filter(
                        tgl_mulai__year=parsed_year
                    ).order_by('tgl_mulai')
                elif parsed_month:
                    # Filter berdasarkan bulan spesifik pada tahun saat ini (real-time)
                    current_year = timezone.now().year
                    queryset = queryset.filter(
                        tgl_mulai__year=current_year,
                        tgl_mulai__month=parsed_month
                    ).order_by('tgl_mulai')
                else:
                    queryset = queryset.order_by('tgl_mulai')


        return queryset.distinct() # distinct untuk menghindari duplikasi jika relasi kompleks

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
@csrf_exempt
def update_kegiatan(request, id):
    try:
        # Ambil kegiatan berdasarkan ID
        kegiatan = Kegiatan.objects.get(id=id)

        # Validasi bahwa hanya pembuat kegiatan yang dapat mengedit
        if kegiatan.user_fk != request.user:
            return Response(
                {'success': False, 'error': 'Anda tidak memiliki izin untuk mengedit kegiatan ini'},
                status=status.HTTP_403_FORBIDDEN
            )

        data = request.data
        nama = data.get('nama')
        deskripsi = data.get('deskripsi', '')
        tgl_mulai = parse_datetime(data.get('start'))
        tgl_selesai = parse_datetime(data.get('end')) if data.get('end') else tgl_mulai.replace(hour=23, minute=59, second=59)
        kategori_id = data.get('kategori_id')

        # Validasi input
        if not all([nama, tgl_mulai, kategori_id]):
            return Response(
                {'success': False, 'error': 'Nama, tanggal mulai, dan kategori wajib diisi'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if tgl_selesai < tgl_mulai:
            return Response(
                {'success': False, 'error': 'Tanggal dan waktu selesai tidak boleh sebelum tanggal dan waktu mulai'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Ambil kategori berdasarkan ID
        try:
            kategori = Kategori.objects.get(id=kategori_id)
        except Kategori.DoesNotExist:
            return Response(
                {'success': False, 'error': 'Kategori tidak ditemukan'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Update kegiatan
        kegiatan.nama = nama
        kegiatan.deskripsi = deskripsi
        kegiatan.tgl_mulai = tgl_mulai
        kegiatan.tgl_selesai = tgl_selesai
        kegiatan.kategori_fk = kategori
        kegiatan.save()
        
        User = get_user_model()
        users = User.objects.all()

        # Buat atau perbarui notifikasi untuk semua user
        for user in users:
            notifikasi, created = Notifikasi.objects.get_or_create(
                user_fk=user,
                kegiatan_fk=kegiatan,
                defaults={'status': 'Pending', 'metode': 'email', 'one_day_before': False, 'one_hour_before': False}
            )
            # Jika notifikasi sudah ada, perbarui status dan flag
            if not created:
                notifikasi.status = 'Pending'
                notifikasi.one_day_before = False
                notifikasi.one_hour_before = False
                notifikasi.save()
            
            send_email_notification.delay(notifikasi.id)

        return Response(
            {'success': True, 'message': 'Kegiatan berhasil diperbarui dan notifikasi dikirimkan'},
            status=status.HTTP_200_OK
        )

    except Kegiatan.DoesNotExist:
        return Response(
            {'success': False, 'error': 'Kegiatan tidak ditemukan'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'success': False, 'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
@csrf_exempt
def delete_kegiatan(request, id):
    try:
        # Ambil kegiatan berdasarkan ID
        kegiatan = Kegiatan.objects.get(id=id)

        # Validasi bahwa hanya pembuat kegiatan yang dapat menghapus
        if kegiatan.user_fk != request.user:
            return Response(
                {'success': False, 'error': 'Anda tidak memiliki izin untuk menghapus kegiatan ini'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Hapus kegiatan
        kegiatan.is_deleted = True
        kegiatan.save()

        return Response(
            {'success': True, 'message': 'Kegiatan berhasil dihapus'},
            status=status.HTTP_200_OK
        )

    except Kegiatan.DoesNotExist:
        return Response(
            {'success': False, 'error': 'Kegiatan tidak ditemukan'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'success': False, 'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

def kalender(request):
    return render(request, 'kalender/kalenderAkademik.html', {
        'user_id': request.user.id if request.user.is_authenticated else None,
    })