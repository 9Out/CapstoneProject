from rest_framework import serializers
from .models import Kegiatan, Kategori
from django.utils import timezone
from datetime import timedelta

# Serializer untuk model Kategori
class KategoriSerializer(serializers.ModelSerializer):
    """Mengonversi data Kategori ke format JSON"""
    class Meta:
        model = Kategori
        fields = ['id', 'nama', 'warna']

# Serializer untuk model Kegiatan
class KegiatanSerializer(serializers.ModelSerializer):
    """Mengonversi data Kegiatan ke format JSON dengan penyesuaian untuk FullCalendar"""
    backgroundColor = serializers.CharField(source='kategori_fk.warna', read_only=True)  # Warna latar dari kategori
    borderColor = serializers.CharField(source='kategori_fk.warna', read_only=True)    # Warna border dari kategori
    title = serializers.CharField(source='nama')                                       # Nama kegiatan sebagai judul
    start = serializers.DateTimeField(source='tgl_mulai')                              # Tanggal mulai kegiatan
    end = serializers.DateTimeField(source='tgl_selesai', allow_null=True)             # Tanggal selesai kegiatan
    user_fk = serializers.PrimaryKeyRelatedField(read_only=True)                       # ID pengguna terkait

    class Meta:
        model = Kegiatan
        fields = ['id', 'title', 'start', 'end', 'nama', 'deskripsi', 'kategori_fk', 'backgroundColor', 'borderColor', 'user_fk']

    def to_representation(self, instance):
        """Menyesuaikan format output untuk kebutuhan frontend"""
        data = super().to_representation(instance)
        kategori = instance.kategori_fk
        # Konversi ke WIB dan ambil tanggal
        start_date = timezone.localtime(instance.tgl_mulai, timezone.get_fixed_timezone(420)).date() if instance.tgl_mulai else None
        end_date = timezone.localtime(instance.tgl_selesai, timezone.get_fixed_timezone(420)).date() if instance.tgl_selesai else None
        if end_date:
            end_date += timedelta(days=1)  # Penyesuaian untuk FullCalendar (end date eksklusif)
        return {
            'id': data['id'],
            'title': data['nama'],
            'start': start_date.isoformat() if start_date else None,
            'end': end_date.isoformat() if end_date else None,
            'deskripsi': instance.deskripsi,
            'kategori': kategori.nama,
            'kategori_id': kategori.id,
            'backgroundColor': kategori.warna,
            'borderColor': kategori.warna,
            'user_fk': instance.user_fk.id,
        }