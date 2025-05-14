from rest_framework import serializers
from .models import Kegiatan, Kategori
from django.utils import timezone
from datetime import timedelta

class KategoriSerializer(serializers.ModelSerializer):
    class Meta:
        model = Kategori
        fields = ['id', 'nama', 'warna']

class KegiatanSerializer(serializers.ModelSerializer):
    backgroundColor = serializers.CharField(source='kategori_fk.warna', read_only=True)
    borderColor = serializers.CharField(source='kategori_fk.warna', read_only=True)
    textColor = serializers.CharField(default='#ffffff', read_only=True)
    title = serializers.CharField(source='nama')
    start = serializers.DateTimeField(source='tgl_mulai')
    end = serializers.DateTimeField(source='tgl_selesai', allow_null=True)
    description = serializers.CharField(allow_blank=True, allow_null=True)
    user_fk = serializers.PrimaryKeyRelatedField(read_only=True)
    
    class Meta:
        model = Kegiatan
        fields = [
            'id', 'title', 'start', 'end', 'description',
            'backgroundColor', 'borderColor', 'textColor',
            'nama', 'tgl_mulai', 'tgl_selesai', 'semester',
            'tahun_akademik', 'kategori_fk', 'user_fk'
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        kategori = instance.kategori_fk
        thAkademik = instance.tahun_akademik
        
        # Konversi ke WIB dan ambil tanggal saja
        start_date = timezone.localtime(instance.tgl_mulai, timezone.get_fixed_timezone(420)).date() if instance.tgl_mulai else None
        end_date = timezone.localtime(instance.tgl_selesai, timezone.get_fixed_timezone(420)).date() if instance.tgl_selesai else None
        
        # Tambah 1 hari ke end_date agar inklusif di FullCalendar
        if end_date:
            end_date = end_date + timedelta(days=1)
        
        return {
            'id': data['id'],
            'tahun_akademik': thAkademik.tahun_akademik,
            'title': data['nama'],
            'start': start_date.isoformat() if start_date else None,
            'end': end_date.isoformat() if end_date else None,
            'deskripsi': instance.deskripsi,
            'kategori': kategori.nama,
            'kategori_id': instance.kategori_fk.id,
            'backgroundColor': kategori.warna,
            'borderColor': kategori.warna,
            'user_fk': instance.user_fk.id,
        }