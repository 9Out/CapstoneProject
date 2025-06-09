from django.shortcuts import render, get_object_or_404
from rest_framework import generics
from .serializers import KegiatanSerializer, KategoriSerializer
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from .models import Notifikasi, Kegiatan, Kategori
from .tasks import send_email_notification, send_whatsapp_notification, check_notifications
from django.utils.dateparse import parse_datetime
from django.utils import timezone
from django.contrib.auth import get_user_model
from ormawa.models import Ormawa
from django.db import transaction

# Create your views here.

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def category_list(request):
    user = request.user
    is_leader = Ormawa.objects.filter(user=user, ketua=user).exists() or Ormawa.objects.filter(user=user, sekretaris=user).exists()
    if is_leader:
        # Hanya kembalikan kategori dengan is_ormawa=True
        categories = Kategori.objects.filter(is_ormawa=True)
    else:
        # Kembalikan semua kategori
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
        tgl_selesai = parse_datetime(data.get('end')) if data.get('end') else tgl_mulai.replace(hour=23, minute=59, second=59)
        kategori_id = data.get('kategori_id')
        semester = data.get('semester', 'Ganjil')
        is_public = data.get('is_public', True)
        ormawa_id = data.get('ormawa_id')
        notify_to = data.get('notify_to', 'all' if is_public else 'ormawa')
        notify_email = data.get('notify_email', True)
        notify_whatsapp = data.get('notify_whatsapp', False)
        reminders = data.get('reminders', [])

        is_leader = Ormawa.objects.filter(user=request.user, ketua=request.user).exists() or Ormawa.objects.filter(user=request.user, sekretaris=request.user).exists()

        if is_leader and ormawa_id:
            try:
                ormawa_category = Kategori.objects.get(nama='Ormawa', is_ormawa=True)
                kategori_id = ormawa_category.id
            except Kategori.DoesNotExist:
                return Response(
                    {'success': False, 'error': 'Kategori Ormawa tidak ditemukan'},
                    status=status.HTTP_404_NOT_FOUND
                )

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
            if is_leader and not kategori.is_ormawa:
                return Response(
                    {'success': False, 'error': 'Hanya kategori Ormawa yang diperbolehkan untuk ketua/sekretaris'},
                    status=status.HTTP_403_FORBIDDEN
                )
        except Kategori.DoesNotExist:
            return Response(
                {'success': False, 'error': 'Kategori tidak ditemukan'},
                status=status.HTTP_404_NOT_FOUND
            )

        ormawa = None
        if ormawa_id:
            try:
                ormawa = Ormawa.objects.get(id=ormawa_id)
                if request.user != ormawa.ketua and request.user != ormawa.sekretaris:
                    return Response(
                        {'success': False, 'error': 'Hanya ketua atau sekretaris yang boleh menambahkan kegiatan untuk Ormawa ini'},
                        status=status.HTTP_403_FORBIDDEN
                    )
                if request.user not in ormawa.user.all():
                    return Response(
                        {'success': False, 'error': 'Anda bukan anggota Ormawa ini'},
                        status=status.HTTP_403_FORBIDDEN
                    )
            except Ormawa.DoesNotExist:
                return Response(
                    {'success': False, 'error': 'Ormawa tidak ditemukan'},
                    status=status.HTTP_404_NOT_FOUND
                )

        with transaction.atomic():
            kegiatan = Kegiatan.objects.create(
                nama=nama,
                deskripsi=deskripsi,
                tgl_mulai=tgl_mulai,
                tgl_selesai=tgl_selesai,
                user_fk=request.user,
                kategori_fk=kategori,
                is_public=is_public,
                ormawa_fk=ormawa
            )

            User = get_user_model()
            if notify_to == 'all':
                users = User.objects.all()
            elif notify_to == 'ormawa':
                users = kegiatan.ormawa_fk.user.all() if kegiatan.ormawa_fk else []
            else:
                return Response(
                    {'success': False, 'error': 'Nilai notify_to tidak valid'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            for user in users:
                if notify_email:
                    notifikasi, created = Notifikasi.objects.get_or_create(
                        user_fk=user,
                        kegiatan_fk=kegiatan,
                        metode='email',
                        defaults={'status': 'Pending', 'action_type': 'create', 'reminders': reminders if reminders else None}
                    )
                    if not created:
                        notifikasi.status = 'Pending'
                        notifikasi.action_type = 'create'
                        notifikasi.reminders = reminders if reminders else None
                        notifikasi.save()
                    transaction.on_commit(lambda n=notifikasi.id: send_email_notification.delay(n))
                    if reminders:
                        transaction.on_commit(lambda: check_notifications.delay())

                if notify_whatsapp:
                    notifikasi, created = Notifikasi.objects.get_or_create(
                        user_fk=user,
                        kegiatan_fk=kegiatan,
                        metode='whatsapp',
                        defaults={'status': 'Pending', 'action_type': 'create', 'reminders': reminders if reminders else None}
                    )
                    if not created:
                        notifikasi.status = 'Pending'
                        notifikasi.action_type = 'create'
                        notifikasi.reminders = reminders if reminders else None
                        notifikasi.save()
                    # Hanya panggil send_whatsapp_notification untuk notifikasi awal jika tidak ada reminders
                    if not reminders or not any(r.get('days', 0) > 0 or r.get('time') != '00:00' for r in reminders):
                        transaction.on_commit(lambda n=notifikasi.id: send_whatsapp_notification.delay(n))
                    if reminders:
                        transaction.on_commit(lambda: check_notifications.delay())

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
def add_kegiatan(request):
    data = request.data
    user = request.user

    # Ambil parameter kunci dari frontend untuk menentukan intensi
    ormawa_id = data.get('ormawa_id')
    notify_to = data.get('notify_to') # 'ormawa', 'all', atau 'self'
    
    # Inisialisasi variabel
    ormawa = None
    kategori = None
    is_public = data.get('is_public', False) # Ambil nilai dari frontend, akan diverifikasi

    # --- Verifikasi Izin Berdasarkan Intensi dari Frontend ---
    try:
        if ormawa_id:
            # 1. Intensi: Membuat kegiatan Ormawa
            ormawa = get_object_or_404(Ormawa, id=ormawa_id)
            if not (user == ormawa.ketua or user == ormawa.sekretaris):
                return Response({'success': False, 'error': 'Hanya ketua/sekretaris yang boleh menambah kegiatan untuk Ormawa ini.'}, status=status.HTTP_403_FORBIDDEN)
            kategori = get_object_or_404(Kategori, nama='Ormawa', is_ormawa=True)
            # is_public dan notify_to sudah diatur dengan benar dari frontend

        elif notify_to == 'self':
            # 2. Intensi: Membuat kegiatan pribadi
            if not user.has_perm('kalender.add_kegiatan_self'):
                return Response({'success': False, 'error': 'Anda tidak memiliki izin untuk menambah kegiatan pribadi.'}, status=status.HTTP_403_FORBIDDEN)
            is_public = False  # Paksa False di backend untuk keamanan
            ormawa = None
            kategori = get_object_or_404(Kategori, id=data.get('kategori_id'))

        elif notify_to == 'all':
            # 3. Intensi: Membuat kegiatan publik
            if not user.has_perm('kalender.add_kegiatan'):
                return Response({'success': False, 'error': 'Anda tidak memiliki izin untuk menambah kegiatan publik.'}, status=status.HTTP_403_FORBIDDEN)
            is_public = True  # Paksa True di backend untuk keamanan
            ormawa = None
            kategori = get_object_or_404(Kategori, id=data.get('kategori_id'))
        
        else:
            return Response({'success': False, 'error': 'Tipe kegiatan tidak valid atau tidak diizinkan.'}, status=status.HTTP_400_BAD_REQUEST)

    except (Kategori.DoesNotExist):
        return Response({'success': False, 'error': 'Kategori tidak ditemukan.'}, status=status.HTTP_404_NOT_FOUND)

    # --- Lanjutkan validasi dan pembuatan objek ---
    nama = data.get('nama')
    tgl_mulai_str = data.get('start')
    if not all([nama, tgl_mulai_str]):
        return Response({'success': False, 'error': 'Nama dan tanggal mulai wajib diisi.'}, status=status.HTTP_400_BAD_REQUEST)
        
    try:
        tgl_mulai = parse_datetime(tgl_mulai_str)
        tgl_selesai = parse_datetime(data.get('end')) if data.get('end') else tgl_mulai.replace(hour=23, minute=59, second=59)
        if tgl_selesai < tgl_mulai:
            return Response({'success': False, 'error': 'Tanggal selesai tidak boleh sebelum tanggal mulai.'}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            kegiatan = Kegiatan.objects.create(
                nama=nama,
                deskripsi=data.get('deskripsi', ''),
                tgl_mulai=tgl_mulai,
                tgl_selesai=tgl_selesai,
                user_fk=user,
                kategori_fk=kategori,
                is_public=is_public,
                ormawa_fk=ormawa
            )

            # --- Logika Notifikasi Terpusat ---
            User = get_user_model()
            users_to_notify = []
            if notify_to == 'all':
                users_to_notify = User.objects.all()
            elif notify_to == 'ormawa' and kegiatan.ormawa_fk:
                users_to_notify = kegiatan.ormawa_fk.user.all()
            elif notify_to == 'self':
                users_to_notify = [user]

            notify_email = data.get('notify_email', False)
            notify_whatsapp = data.get('notify_whatsapp', False)
            reminders = data.get('reminders', [])

            for target_user in users_to_notify:
                if notify_email:
                    notif = Notifikasi.objects.create(user_fk=target_user, kegiatan_fk=kegiatan, metode='email', reminders=reminders, action_type='create')
                    transaction.on_commit(lambda n_id=notif.id: send_email_notification.delay(n_id))

                if notify_whatsapp:
                    notif = Notifikasi.objects.create(user_fk=target_user, kegiatan_fk=kegiatan, metode='whatsapp', reminders=reminders, action_type='create')
                    transaction.on_commit(lambda n_id=notif.id: send_whatsapp_notification.delay(n_id))

            if reminders and (notify_email or notify_whatsapp):
                transaction.on_commit(check_notifications.delay)

        return Response({'success': True, 'message': 'Kegiatan berhasil ditambahkan'}, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({'success': False, 'error': f'Terjadi kesalahan: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class KegiatanListView(generics.ListAPIView):
    serializer_class = KegiatanSerializer

    def get_queryset(self):
        queryset = Kegiatan.objects.filter(is_deleted=False)
        user = self.request.user
        search = self.request.query_params.get('search')
        start_param = self.request.query_params.get('start')
        end_param = self.request.query_params.get('end')
        year_str = self.request.query_params.get('year')
        month_str = self.request.query_params.get('month')
        academic_year_param = self.request.query_params.get('academic_year')
        user_ormawa = Ormawa.objects.filter(user=user) if user.is_authenticated else Ormawa.objects.none()

        # Filter kegiatan:
        # - Kegiatan publik (is_public=True)
        # - Kegiatan tidak publik (is_public=False) yang user adalah anggota Ormawa-nya
        if user.is_authenticated:
            user_ormawa = Ormawa.objects.filter(user=user)
            queryset = queryset.filter(
            Q(is_public=True) |
            Q(is_public=False, ormawa_fk__in=user_ormawa) |
            Q(is_public=False, ormawa_fk__isnull=True, user_fk=user)
        ).distinct()
        else:
            # Jika user tidak login, hanya tampilkan kegiatan publik
            queryset = queryset.filter(is_public=True)

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
                    queryset = queryset.filter(
                        tgl_mulai__lt=end_date,
                        tgl_selesai__gte=start_date
                    ).order_by('tgl_mulai')
            elif academic_year_param:
                queryset = queryset.filter(tahun_akademik=academic_year_param).order_by('tgl_mulai') 
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
        if kegiatan.user_fk != request.user and not (
            kegiatan.ormawa_fk and (
                request.user == kegiatan.ormawa_fk.ketua or request.user == kegiatan.ormawa_fk.sekretaris
            )
        ):
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
        is_public = data.get('is_public', kegiatan.is_public)
        ormawa_id = data.get('ormawa_id')
        notify_to = data.get('notify_to', 'all' if is_public else 'ormawa')
        notify_email = data.get('notify_email', True)
        notify_whatsapp = data.get('notify_whatsapp', False)
        reminders = data.get('reminders', [])

        is_leader = kegiatan.ormawa_fk and (
            request.user == kegiatan.ormawa_fk.ketua or request.user == kegiatan.ormawa_fk.sekretaris
        )

        if is_leader and ormawa_id:
            try:
                ormawa_category = Kategori.objects.get(nama='Ormawa', is_ormawa=True)
                kategori_id = ormawa_category.id
            except Kategori.DoesNotExist:
                return Response(
                    {'success': False, 'error': 'Kategori Ormawa tidak ditemukan'},
                    status=status.HTTP_404_NOT_FOUND
                )

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

        try:
            kategori = Kategori.objects.get(id=kategori_id)
            if is_leader and not kategori.is_ormawa:
                return Response(
                    {'success': False, 'error': 'Hanya kategori Ormawa yang diperbolehkan untuk ketua/sekretaris'},
                    status=status.HTTP_403_FORBIDDEN
                )
        except Kategori.DoesNotExist:
            return Response(
                {'success': False, 'error': 'Kategori tidak ditemukan'},
                status=status.HTTP_404_NOT_FOUND
            )

        ormawa = None
        if ormawa_id:
            try:
                ormawa = Ormawa.objects.get(id=ormawa_id)
                if request.user != ormawa.ketua and request.user != ormawa.sekretaris:
                    return Response(
                        {'success': False, 'error': 'Hanya ketua atau sekretaris yang boleh mengedit kegiatan untuk Ormawa ini'},
                        status=status.HTTP_403_FORBIDDEN
                    )
                if request.user not in ormawa.user.all():
                    return Response(
                        {'success': False, 'error': 'Anda bukan anggota Ormawa ini'},
                        status=status.HTTP_403_FORBIDDEN
                    )
            except Ormawa.DoesNotExist:
                return Response(
                    {'success': False, 'error': 'Ormawa tidak ditemukan'},
                    status=status.HTTP_404_NOT_FOUND
                )

        with transaction.atomic():
            kegiatan.nama = nama
            kegiatan.deskripsi = deskripsi
            kegiatan.tgl_mulai = tgl_mulai
            kegiatan.tgl_selesai = tgl_selesai
            kegiatan.kategori_fk = kategori
            kegiatan.is_public = is_public
            kegiatan.ormawa_fk = ormawa
            kegiatan.save()

            User = get_user_model()
            if notify_to == 'all':
                users = User.objects.all()
            elif notify_to == 'ormawa':
                users = kegiatan.ormawa_fk.user.all() if kegiatan.ormawa_fk else []
            else:
                return Response(
                    {'success': False, 'error': 'Nilai notify_to tidak valid'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            for user in users:
                if notify_email:
                    notifikasi, created = Notifikasi.objects.get_or_create(
                        user_fk=user,
                        kegiatan_fk=kegiatan,
                        metode='email',
                        defaults={'status': 'Pending', 'action_type': 'update', 'reminders': reminders if reminders else None}
                    )
                    if not created:
                        notifikasi.status = 'Pending'
                        notifikasi.action_type = 'update'
                        notifikasi.reminders = reminders if reminders else None
                        notifikasi.save()
                    # Panggil task untuk setiap notifikasi secara individual
                    transaction.on_commit(lambda n=notifikasi.id: send_email_notification.delay(n))
                    if reminders:
                        transaction.on_commit(lambda: check_notifications.delay())

                if notify_whatsapp:
                    notifikasi, created = Notifikasi.objects.get_or_create(
                        user_fk=user,
                        kegiatan_fk=kegiatan,
                        metode='whatsapp',
                        defaults={'status': 'Pending', 'action_type': 'update', 'reminders': reminders if reminders else None}
                    )
                    if not created:
                        notifikasi.status = 'Pending'
                        notifikasi.action_type = 'update'
                        notifikasi.reminders = reminders if reminders else None
                        notifikasi.save()
                    # Panggil task untuk setiap notifikasi secara individual
                    transaction.on_commit(lambda n=notifikasi.id: send_whatsapp_notification.delay(n))
                    if reminders:
                        transaction.on_commit(lambda: check_notifications.delay())

        return Response(
            {'success': True, 'message': 'Kegiatan berhasil diperbarui dan notifikasi diperbarui'},
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
        kegiatan = Kegiatan.objects.get(id=id)
        if kegiatan.user_fk != request.user:
            return Response(
                {'success': False, 'error': 'Anda tidak memiliki izin untuk menghapus kegiatan ini'},
                status=status.HTTP_403_FORBIDDEN
            )

        User = get_user_model()
        notify_to = request.data.get('notify_to', 'all' if kegiatan.is_public else 'ormawa')
        if notify_to == 'all':
            users = User.objects.all()
        elif notify_to == 'ormawa':
            users = kegiatan.ormawa_fk.user.all() if kegiatan.ormawa_fk else []
        else:
            return Response(
                {'success': False, 'error': 'Nilai notify_to tidak valid'},
                status=status.HTTP_400_BAD_REQUEST
            )

        notifikasi_list = Notifikasi.objects.filter(kegiatan_fk=kegiatan)

        for user in users:
            user_notifikasi_list = notifikasi_list.filter(user_fk=user)
            for notifikasi in user_notifikasi_list:
                notifikasi.status = 'Pending'
                notifikasi.action_type = 'delete'
                notifikasi.save()
                if notifikasi.metode == 'email':
                    transaction.on_commit(lambda: send_email_notification.delay(notifikasi.id))
                elif notifikasi.metode == 'whatsapp':
                    transaction.on_commit(lambda: send_whatsapp_notification.delay(notifikasi.id))

        kegiatan.is_deleted = True
        kegiatan.save()

        return Response(
            {'success': True, 'message': 'Kegiatan berhasil dihapus dan notifikasi dikirim'},
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
        
@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def save_notification_reminders(request):
    try:
        data = request.data
        kegiatan_id = data.get('kegiatan_id')
        metode = data.get('metode')
        reminders = data.get('reminders', [])  # Daftar pengingat dari form

        if not kegiatan_id or not metode:
            return Response(
                {'success': False, 'error': 'Kegiatan ID dan metode wajib diisi'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            kegiatan = Kegiatan.objects.get(id=kegiatan_id)
        except Kegiatan.DoesNotExist:
            return Response(
                {'success': False, 'error': 'Kegiatan tidak ditemukan'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Cek izin: pemilik kegiatan, anggota Ormawa, atau memiliki izin add_notifikasi
        has_permission = (
            kegiatan.user_fk == request.user or
            (kegiatan.ormawa_fk and request.user in kegiatan.ormawa_fk.user.all()) or
            request.user.has_perm('kalender.add_notifikasi')
        )
        if not has_permission:
            return Response(
                {'success': False, 'error': 'Anda tidak memiliki izin untuk mengatur notifikasi kegiatan ini'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Hapus notifikasi lama 
        Notifikasi.objects.filter(user_fk=request.user, kegiatan_fk=kegiatan, metode=metode).delete()

        # Buat notifikasi baru dengan pengingat
        notifikasi = Notifikasi.objects.create(
            user_fk=request.user,
            kegiatan_fk=kegiatan,
            metode=metode,
            status='Pending',
            action_type='reminder', 
            reminders=reminders
        )
        transaction.on_commit(lambda: check_notifications.delay()) 

        return Response(
            {'success': True, 'message': 'Pengingat notifikasi berhasil disimpan'},
            status=status.HTTP_201_CREATED
        )

    except Exception as e:
        return Response(
            {'success': False, 'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_ormawa_list(request):
    try:
        ormawa_list = Ormawa.objects.filter(user=request.user)
        ormawa_data = []
        is_leader = False  #

        for ormawa in ormawa_list:
            is_ketua = request.user == ormawa.ketua
            is_sekretaris = request.user == ormawa.sekretaris
            if is_ketua or is_sekretaris:
                is_leader = True
            ormawa_data.append({
                'id': ormawa.id,
                'nama': ormawa.nama,
                'is_ketua': is_ketua,
                'is_sekretaris': is_sekretaris
            })

        return Response({
            'ormawa_list': ormawa_data,
            'is_leader': is_leader
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def kalender(request):
    is_leader = False
    can_add_self_kegiatan = False
    can_add_public_kegiatan = False 

    if request.user.is_authenticated:
        if Ormawa.objects.filter(Q(ketua=request.user) | Q(sekretaris=request.user)).exists():
            is_leader = True

        if request.user.has_perm('kalender.add_kegiatan_self'):
            can_add_self_kegiatan = True
            
        if request.user.has_perm('kalender.add_kegiatan'):
            can_add_public_kegiatan = True

    context = {
        'user_id': request.user.id if request.user.is_authenticated else None,
        'is_leader': is_leader, 
        'can_add_self_kegiatan': can_add_self_kegiatan,
        'can_add_public_kegiatan': can_add_public_kegiatan, # BARU
    }
    return render(request, 'kalender/kalenderAkademik.html', context)