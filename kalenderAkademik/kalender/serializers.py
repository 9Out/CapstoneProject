from rest_framework import serializers
from .models import Kegiatan, Notifikasi
from django.utils import timezone
from datetime import timedelta

class KegiatanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Kegiatan
        fields = ['id', 'nama', 'tgl_mulai', 'tgl_selesai', 'semester', 'tahun_akademik', 'deskripsi']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        kategori = instance.kategori_fk
        
        # Konversi ke WIB dan ambil tanggal saja
        start_date = timezone.localtime(instance.tgl_mulai, timezone.get_fixed_timezone(420)).date() if instance.tgl_mulai else None
        end_date = timezone.localtime(instance.tgl_selesai, timezone.get_fixed_timezone(420)).date() if instance.tgl_selesai else None
        
        # Tambah 1 hari ke end_date agar inklusif di FullCalendar
        if end_date:
            end_date = end_date + timedelta(days=1)
        
        return {
            'id': data['id'],
            'title': data['nama'],
            'start': start_date.isoformat() if start_date else None,
            'end': end_date.isoformat() if end_date else None,
            'deskripsi': data.get('deskripsi', ''),
            'kategori': kategori.nama,
            'backgroundColor': kategori.warna,
            'borderColor': kategori.warna
        }