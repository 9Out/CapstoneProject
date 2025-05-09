from rest_framework import serializers
from .models import Kegiatan

class KegiatanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Kegiatan
        fields = '__all__'  # Ini akan otomatis ambil semua field dari model
