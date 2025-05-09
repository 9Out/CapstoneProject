from django.conf import settings
from django.db import models

# from django.contrib.auth.models import User
# Create your models here.

class Kategori(models.Model):
    nama = models.CharField(max_length=25)
    def __str__(self):
        return self.nama

class Kegiatan(models.Model):
    nama = models.CharField(max_length=50)
    deskripsi = models.CharField(max_length=254, blank=True, null=True)
    tgl_mulai = models.DateTimeField()
    tgl_selesai = models.DateTimeField()
    user_fk = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    kategori_fk = models.ForeignKey(Kategori, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nama

class Notifikasi(models.Model):
    user_fk = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    kegiatan_fk = models.ForeignKey(Kegiatan, on_delete=models.CASCADE)
    pesan = models.CharField(max_length=254, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notifikasi untuk {self.user_fk}: {self.pesan}"
