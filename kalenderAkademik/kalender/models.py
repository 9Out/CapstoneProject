from django.conf import settings
from django.db import models


class TahunAkademik(models.Model):
    tahun_akademik = models.CharField(max_length=10)
    def _str_(self):
        return self.tahun_akademik

class Kategori(models.Model):
    nama = models.CharField(max_length=25)
    def _str_(self):
        return self.nama

class Kegiatan(models.Model):
    tahun_akademik = models.ForeignKey(TahunAkademik, on_delete=models.CASCADE)
    semester = models.CharField(choices=[('ganjil','Ganjil'),('genap','Genap')], max_length=20, default='ganjil')
    nama = models.CharField(max_length=50)
    deskripsi = models.CharField(max_length=254, blank=True, null=True)
    tgl_mulai = models.DateTimeField()
    tgl_selesai = models.DateTimeField()
    user_fk = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    kategori_fk = models.ForeignKey(Kategori, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def _str_(self):
        return self.nama

class Notifikasi(models.Model):
    user_fk = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    kegiatan_fk = models.ForeignKey(Kegiatan, on_delete=models.CASCADE)
    pesan = models.CharField(max_length=254, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notifikasi untuk {self.user_fk}: {self.pesan}"