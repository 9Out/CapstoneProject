from celery import shared_task
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from .models import Notifikasi
from django.conf import settings
import pytz
from datetime import datetime, timedelta
import requests
import re


def format_no_telpon(no_telpon):
    no_telpon = re.sub(r'[^0-9+]', '', no_telpon)
    if no_telpon.startswith('+62'):
        return no_telpon
    if no_telpon.startswith('0'):
        no_telpon = '+62' + no_telpon[1:]
    elif no_telpon.startswith('62'):
        no_telpon = '+' + no_telpon
    if not re.match(r'^\+62\d{9,}$', no_telpon):
        raise ValueError(f"Nomor telepon tidak valid: {no_telpon}")
    return no_telpon

@shared_task
def send_email_notification(notifikasi_id, is_scheduled=False):
    try:
        notifikasi = Notifikasi.objects.select_related('kegiatan_fk__ormawa_fk').get(id=notifikasi_id)
        if notifikasi.metode != 'email':
            return

        nama_lengkap = f"{notifikasi.user_fk.first_name} {notifikasi.user_fk.last_name}".strip() or notifikasi.user_fk.username
        wib_tz = pytz.timezone('Asia/Jakarta')
        tgl_mulai_wib = notifikasi.kegiatan_fk.tgl_mulai.replace(tzinfo=pytz.UTC).astimezone(wib_tz)
        tgl_selesai_wib = notifikasi.kegiatan_fk.tgl_selesai.replace(tzinfo=pytz.UTC).astimezone(wib_tz)
        tgl_mulai_formatted = tgl_mulai_wib.strftime('%d-%m-%Y')
        waktu_mulai_formatted = tgl_mulai_wib.strftime('%H:%M WIB')
        tgl_selesai_formatted = tgl_selesai_wib.strftime('%d-%m-%Y')
        waktu_selesai_formatted = tgl_selesai_wib.strftime('%H:%M WIB')

        email_pengguna = notifikasi.user_fk.email
        kegiatan = notifikasi.kegiatan_fk

        if not is_scheduled:
            if notifikasi.action_type == 'create':
                subject = f"Kegiatan Baru: {kegiatan.nama}"
                pesan = f"Ada kegiatan baru yang mungkin menarik untuk Anda."
            elif notifikasi.action_type == 'update':
                subject = f"Perubahan Jadwal: {kegiatan.nama}"
                pesan = f"Ada perubahan jadwal pada kegiatan berikut."
            else: 
                subject = f"Pembatalan Kegiatan: {kegiatan.nama}"
                pesan = f"Kegiatan berikut telah dibatalkan."
        else:
            subject = f"Pengingat: {kegiatan.nama}"
            pesan = f"Ini adalah pengingat untuk kegiatan berikut."

        ormawa_nama = kegiatan.ormawa_fk.nama if kegiatan.ormawa_fk else None
        from_email = settings.EMAIL_HOST_USER
        recipient_list = [email_pengguna]
        
        html_content = render_to_string('email.html', {
            'nama': nama_lengkap,
            'pesan': pesan,
            'kegiatan': kegiatan.nama,
            'tgl_mulai': tgl_mulai_formatted,
            'waktu_mulai': waktu_mulai_formatted,
            'tgl_selesai': tgl_selesai_formatted,
            'waktu_selesai': waktu_selesai_formatted,
            'semester': kegiatan.semester,
            'tahun_ajaran': kegiatan.tahun_akademik,
            'action_type': notifikasi.action_type,
            'ormawa_nama': ormawa_nama,
        })

        email = EmailMultiAlternatives(subject, '', from_email, recipient_list)
        email.attach_alternative(html_content, "text/html")
        email.send()

        if is_scheduled:
            reminder_key = f"{next(iter(notifikasi.reminders or [{}])).get('days', 0)}_day_{next(iter(notifikasi.reminders or [{}])).get('time', '09:00').replace(':', '_')}"
            notifikasi.sent_reminders[reminder_key] = True
            notifikasi.save()

    except Exception as e:
        notifikasi.status = 'Gagal'
        notifikasi.save()
        raise e

@shared_task
def send_whatsapp_notification(notifikasi_id):
    try:
        # Preload kegiatan_fk dan ormawa_fk
        notifikasi = Notifikasi.objects.select_related('kegiatan_fk__ormawa_fk').get(id=notifikasi_id)
        if notifikasi.metode != 'whatsapp':
            return

        nama_lengkap = f"{notifikasi.user_fk.first_name} {notifikasi.user_fk.last_name}".strip() or notifikasi.user_fk.username
        nomor_whatsapp = notifikasi.user_fk.no_telpon

        formatted_number = format_no_telpon(nomor_whatsapp)

        wib_tz = pytz.timezone('Asia/Jakarta')
        tgl_mulai_wib = notifikasi.kegiatan_fk.tgl_mulai.replace(tzinfo=pytz.UTC).astimezone(wib_tz)
        tgl_mulai_formatted = tgl_mulai_wib.strftime('%d-%m-%Y')
        tgl_selesai_wib = notifikasi.kegiatan_fk.tgl_selesai.replace(tzinfo=pytz.UTC).astimezone(wib_tz)
        tgl_selesai_formatted = tgl_selesai_wib.strftime('%d-%m-%Y')
        
        # Ambil nama Ormawa dari kegiatan
        ormawa_nama = notifikasi.kegiatan_fk.ormawa_fk.nama if notifikasi.kegiatan_fk.ormawa_fk else None
        
        ormawa_text = f" (oleh {ormawa_nama})" if ormawa_nama else ""

        # Sesuaikan pesan berdasarkan action_type
        if notifikasi.action_type == 'create':
            message = (
                f"Hai, Kak👋 {nama_lengkap},\n\n"
                f"Ada kegiatan baru: *{notifikasi.kegiatan_fk.nama}*{ormawa_text}\n"
                f"Tanggal: {tgl_mulai_formatted} s.d. {tgl_selesai_formatted}\n\n"
                "Jangan lupa ya😉\n"
            )
        elif notifikasi.action_type == 'update':
            message = (
                f"Hai, Kak👋 {nama_lengkap},\n\n"
                f"Ada perubahan jadwal kegiatan: *{notifikasi.kegiatan_fk.nama}*{ormawa_text}\n"
                f"Tanggal: {tgl_mulai_formatted} s.d. {tgl_selesai_formatted}\n\n"
                "Harap diperhatikan ya😉\n"
            )
        else:  # action_type == 'delete'
            message = (
                f"Hai, Kak👋 {nama_lengkap},\n\n"
                f"Kegiatan berikut telah dibatalkan: *{notifikasi.kegiatan_fk.nama}*{ormawa_text}\n"
                f"Tanggal: {tgl_mulai_formatted} s.d. {tgl_selesai_formatted}\n\n"
                "Terima kasih atas perhatiannya.\n"
            )

        response = requests.post('http://localhost:3000/send-message', json={
            'phone': formatted_number,
            'message': message
        })
        response.raise_for_status()

        notifikasi.status = 'Terkirim'
        notifikasi.save()

    except Exception as e:
        notifikasi.status = 'Gagal'
        notifikasi.save()
        raise e

@shared_task
def check_notifications():
    wib_tz = pytz.timezone('Asia/Jakarta')
    now = datetime.now(pytz.UTC).astimezone(wib_tz)
    notifikasi_list = Notifikasi.objects.filter(status='Pending', action_type='reminder')

    for notifikasi in notifikasi_list:
        tgl_mulai_wib = notifikasi.kegiatan_fk.tgl_mulai.replace(tzinfo=pytz.UTC).astimezone(wib_tz)
        for reminder in notifikasi.reminders:
            days = reminder.get('days', 0)
            time = reminder.get('time', '09:00')
            reminder_key = f"{days}_day_{time.replace(':', '_')}"  # Unique key, e.g., "1_day_09_00"

            if reminder_key in notifikasi.sent_reminders:
                continue 

            reminder_time = tgl_mulai_wib - timedelta(days=days)
            reminder_time = reminder_time.replace(hour=int(time.split(':')[0]), minute=int(time.split(':')[1]), second=0)

            time_difference = (reminder_time - now).total_seconds()
            if 0 <= time_difference <= 3600:  # Within 1 hour window
                if notifikasi.metode == 'whatsapp':
                    send_whatsapp_notification.delay(notifikasi.id, is_scheduled=True)
                elif notifikasi.metode == 'email':
                    send_email_notification.delay(notifikasi.id, is_scheduled=True)
                notifikasi.sent_reminders[reminder_key] = True
                notifikasi.save()