from django.conf import settings
from django.db import models

# Pilihan warna (COLOR_CHOICES)
COLOR_CHOICES = [
    ('#a9a9a9', 'Abu-abu'),
    ('#7a8b8b', 'Abu-abu Biru'),
    ('#6e7b8b', 'Abu-abu Biru Gelap'),
    ('#c1cdc1', 'Abu-abu Hijau'),
    ('#f5f5dc', 'Abu-abu Krem (Beige)'),
    ('#dcdcdc', 'Abu-abu Muda (Gainsboro)'),
    ('#808080', 'Abu-abu Sedang (Gray)'),
    ('#696969', 'Abu-abu Tua (Dim Gray)'),
    ('#778899', 'Abu-abu Terang Kebiruan (Light Slate Gray)'),
    ('#708090', 'Abu-abu Kebiruan (Slate Gray)'),
    # (Untuk menghemat ruang di sini, sisanya tetap gunakan COLOR_CHOICES asli kamu)
    ('#fffafa', 'Putih Salju (Snow)'),
    ('#ffe4c4', 'Bisque'),
    ('#ffc0cb', 'Pink'),
    ('#ffb6c1', 'Pink Muda (Light Pink)'),
    ('#db7093', 'Pink Violet Pucat (Pale Violet Red)'),
    ('#ff69b4', 'Pink Cerah'), 
    ('#ff1493', 'Pink Tua'), 
    ('#ff83fa', 'Orchid Cerah'), 
]

class TahunAkademik(models.Model):
    tahun_akademik = models.CharField(max_length=10)

    def __str__(self):
        return self.tahun_akademik

class Kategori(models.Model):
    nama = models.CharField(max_length=50)
    warna = models.CharField(
        unique=True,
        max_length=7,
        choices=COLOR_CHOICES,
        default='#00205b'
    )

    def __str__(self):
        return self.nama

class Kegiatan(models.Model):
    tahun_akademik = models.ForeignKey(TahunAkademik, on_delete=models.CASCADE)
    semester = models.CharField(
        choices=[('Ganjil', 'Ganjil'), ('Genap', 'Genap')],
        max_length=20,
        default='Ganjil'
    )
    nama = models.CharField(max_length=50)
    deskripsi = models.TextField(max_length=254, blank=True, null=True)
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
    metode = models.CharField(
        choices=[('email', 'Email'), ('whatsapp', 'Whatsapp')],
        max_length=20,
        default='email'
    )
    status = models.CharField(
        choices=[('Pending', 'Pending'), ('Terkirim', 'Terkirim'), ('Gagal', 'Gagal')],
        max_length=20,
        default='Pending'
    )
    one_day_before = models.BooleanField(default=False)
    one_hour_before = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notifikasi untuk {self.user_fk}"