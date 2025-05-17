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
def send_email_notification(notifikasi_id):
    try:
        notifikasi = Notifikasi.objects.get(id=notifikasi_id)
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
        subject = f"Pengingat Kegiatan: {kegiatan.nama}"
        from_email = settings.EMAIL_HOST_USER  
        recipient_list = [email_pengguna]
        
        html_content = render_to_string('email.html', {
            'nama': nama_lengkap,
            'kegiatan': kegiatan.nama,
            'tgl_mulai': tgl_mulai_formatted,
            'waktu_mulai': waktu_mulai_formatted,
            'tgl_selesai': tgl_selesai_formatted,
            'waktu_selesai': waktu_selesai_formatted,
            'semester': kegiatan.semester,
            'tahun_ajaran': kegiatan.tahun_akademik,
        })

        email = EmailMultiAlternatives(subject, '', from_email, recipient_list)
        email.attach_alternative(html_content, "text/html")
        email.send()

        notifikasi.status = 'Terkirim'
        notifikasi.save()

    except Exception as e:
        notifikasi.status = 'Gagal'
        notifikasi.save()
        raise e

@shared_task
def send_whatsapp_notification(notifikasi_id):
    try:
        notifikasi = Notifikasi.objects.get(id=notifikasi_id)
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
        
        # waktu_mulai_formatted = tgl_mulai_wib.strftime('%H:%M WIB')
        
        

        message = (
            f"Hai, Kak👋 {nama_lengkap},\n\n"
            f"Kegiatan yang akan datang: *{notifikasi.kegiatan_fk.nama}*\n"
            f"Tanggal: {tgl_mulai_formatted} s.d. {tgl_selesai_formatted}\n\n"
            "Jangan lupa ya😉\n"
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
    notifikasi_list = Notifikasi.objects.filter(status='Pending')

    for notifikasi in notifikasi_list:
        tgl_mulai_wib = notifikasi.kegiatan_fk.tgl_mulai.replace(tzinfo=pytz.UTC).astimezone(wib_tz)
        time_difference = tgl_mulai_wib - now
        time_difference_seconds = time_difference.total_seconds()

        # 1 hari sebelum (86400 detik)
        if 0 <= time_difference_seconds <= 86400 and not notifikasi.one_day_before:
            if notifikasi.metode == 'whatsapp':
                send_whatsapp_notification.delay(notifikasi.id)
            elif notifikasi.metode == 'email':
                send_email_notification.delay(notifikasi.id)
            notifikasi.one_day_before = True
            notifikasi.save()

        # 1 jam sebelum (3600 detik)
        if 0 <= time_difference_seconds <= 3600 and not notifikasi.one_hour_before:
            if notifikasi.metode == 'whatsapp':
                send_whatsapp_notification.delay(notifikasi.id)
            elif notifikasi.metode == 'email':
                send_email_notification.delay(notifikasi.id)
            notifikasi.one_hour_before = True
            notifikasi.save()