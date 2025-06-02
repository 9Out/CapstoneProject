from rest_framework import serializers
from .models import Kegiatan, Kategori
from django.utils import timezone

# Serializer untuk model Kategori
class KategoriSerializer(serializers.ModelSerializer):
    """Mengonversi data Kategori ke format JSON"""
    class Meta:
        model = Kategori
        fields = ['id', 'nama', 'warna']

# Serializer untuk model Kegiatan
class KegiatanSerializer(serializers.ModelSerializer):
    """Mengonversi data Kegiatan ke format JSON dengan penyesuaian untuk FullCalendar"""
    backgroundColor = serializers.CharField(source='kategori_fk.warna', read_only=True)
    borderColor = serializers.CharField(source='kategori_fk.warna', read_only=True)    
    title = serializers.CharField(source='nama')                                       
    start = serializers.DateTimeField(source='tgl_mulai')                              
    end = serializers.DateTimeField(source='tgl_selesai', allow_null=True)             
    user_fk = serializers.PrimaryKeyRelatedField(read_only=True)    
    ormawa_fk = serializers.PrimaryKeyRelatedField(read_only=True)
    tahun_akademik = serializers.CharField(read_only=True)  

    class Meta:
        model = Kegiatan
        fields = ['id', 'title', 'start', 'end', 'nama', 'deskripsi', 'kategori_fk', 'backgroundColor', 'borderColor', 'user_fk', 'ormawa_fk', 'tahun_akademik', 'semester', 'is_public']
    
    def to_representation(self, instance):
        """Menyesuaikan format output untuk kebutuhan frontend"""
        data = super().to_representation(instance)
        kategori = instance.kategori_fk
        # Konversi ke WIB dan ambil tanggal
        start_date = timezone.localtime(instance.tgl_mulai, timezone.get_fixed_timezone(420)) if instance.tgl_mulai else None
        end_date = timezone.localtime(instance.tgl_selesai, timezone.get_fixed_timezone(420)) if instance.tgl_selesai else None

        # Tentukan allDay berdasarkan perbandingan tanggal
        all_day = False
        if start_date and end_date:
            start_date_stripped = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date_stripped = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
            if start_date_stripped == end_date_stripped:
                all_day = True

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
            'ormawa_fk': instance.ormawa_fk.id if instance.ormawa_fk else None,
            'ormawa_nama': instance.ormawa_fk.nama if instance.ormawa_fk else None,
            'is_public': instance.is_public,
            'allDay': all_day,
            'tahun_akademik': instance.tahun_akademik,  
            'semester': instance.semester,
        }