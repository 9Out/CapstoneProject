from django.conf import settings
from django.db import models

# from django.contrib.auth.models import User
# Create your models here.

class TahunAkademik(models.Model):
    tahun_akademik = models.CharField(max_length=10)
    def __str__(self):
        return self.tahun_akademik

class Kategori(models.Model):
    nama = models.CharField(max_length=25)
    warna = models.CharField(unique=True,
        max_length=7,  
        choices = [
        ('#a9a9a9', 'Abu-abu'),
        ('#7a8b8b', 'Abu-abu Biru'),
        ('#6e7b8b', 'Abu-abu Biru Gelap'),
        ('#c1cdc1', 'Abu-abu Hijau'),
        ('#b22222', 'Merah Bata'),
        ('#cd853f', 'Cokelat Peru'),
        ('#a0522d', 'Cokelat Sienna'),
        ('#deb887', 'Cokelat Burly'),
        ('#d2691e', 'Cokelat Cokelat'),
        ('#f4a460', 'Cokelat Sandy'),
        ('#000000', 'Hitam'),
        ('#00ff00', 'Hijau Terang'),
        ('#00c853', 'Hijau'),
        ('#228b22', 'Hijau Hutan'),
        ('#32cd32', 'Hijau Lime'),
        ('#66cd00', 'Hijau Sedang'),
        ('#adff2f', 'Hijau Kekuningan'),
        ('#b3ee3a', 'Hijau Cerah'),
        ('#76ee00', 'Hijau Cerah'),
        ('#00ff7f', 'Hijau Musim Semi'),
        ('#7fff00', 'Hijau Chartreuse'),
        ('#9acd32', 'Hijau Zaitun'),
        ('#6b8e23', 'Hijau Zaitun Gelap'),
        ('#98fb98', 'Hijau Pucat'),
        ('#9aff9a', 'Hijau Pucat Cerah'),
        ('#00fa9a', 'Hijau Medium'),
        ('#20b2aa', 'Hijau Laut'),
        ('#3cb371', 'Hijau Laut Sedang'),
        ('#66cdaa', 'Hijau Laut Medium'),
        ('#b4eeb4', 'Hijau Mint'),
        ('#ffd700', 'Emas'),
        ('#cdad00', 'Kuning Emas'),
        ('#ffcc00', 'Kuning'),
        ('#e3cf57', 'Kuning Mustard'),
        ('#f0e68c', 'Kuning Pucat'),
        ('#ff7f50', 'Koral'),
        ('#f08080', 'Koral Cerah'),
        ('#ff7256', 'Koral Cerah'),
        ('#e9967a', 'Koral Terang'),
        ('#ff8247', 'Oranye Koral'),
        ('#ffa500', 'Oranye'),
        ('#ff4500', 'Oranye Merah'),
        ('#ff8c00', 'Oranye Tua'),
        ('#ff4040', 'Merah Cerah'),
        ('#ee3b3b', 'Merah Cerah'),
        ('#ff3030', 'Merah Scarlet'),
        ('#ff4444', 'Merah'),
        ('#dc143c', 'Merah Crimson'),
        ('#ff6347', 'Merah Tomat'),
        ('#b03060', 'Merah Maroon'),
        ('#c71585', 'Merah Violet'),
        ('#cd3278', 'Merah Violet Cerah'),
        ('#cd5c5c', 'Merah Muda'),
        ('#eea9b8', 'Merah Muda Sedang'),
        ('#cd9b9b', 'Merah Muda Tua'),
        ('#ff34b3', 'Merah Muda Cerah'),
        ('#ff69b4', 'Pink Cerah'),
        ('#ff1493', 'Pink Tua'),
        ('#ff83fa', 'Orchid Cerah'),
        ('#c0c0c0', 'Perak'),
        ('#ffffff', 'Putih'),
        ('#ffdead', 'Navajo Putih'),
        ('#ff00ff', 'Magenta'),
        ('#8b008b', 'Ungu Magenta'),
        ('#4b0082', 'Ungu Tua'),
        ('#9400d3', 'Ungu Violet Gelap'),
        ('#ee82ee', 'Ungu Violet'),
        ('#663399', 'Ungu Rebecca'),
        ('#9932cc', 'Ungu Gelap'),
        ('#ba55d3', 'Ungu Medium'),
        ('#b452cd', 'Ungu Cerah'),
        ('#cd69c9', 'Ungu Cerah'),
        ('#dda0dd', 'Ungu Plum'),
        ('#da70d6', 'Ungu Orchid'),
        ('#00e5ee', 'Turkis Cerah'),
        ('#7fffd4', 'Turkis Cerah'),
        ('#00ced1', 'Turkis Gelap'),
        ('#afeeee', 'Turkis Pucat'),
        ('#48d1cc', 'Turkis Medium'),
        ('#191970', 'Biru Tengah Malam'),
        ('#00205b', 'Biru Tua'),
        ('#4682b4', 'Biru Baja'),
        ('#5f9ea0', 'Biru Cadet'),
        ('#4169e1', 'Biru Royal'),
        ('#4876ff', 'Biru Cerah'),
        ('#00b7eb', 'Biru Langit'),
        ('#87ceeb', 'Biru Langit Cerah'),
        ('#7ec0ee', 'Biru Langit Sedang'),
        ('#00bfff', 'Biru Langit Dalam'),
        ('#1e90ff', 'Biru Dodger'),
        ('#6ca6cd', 'Biru Periwinkle'),
        ('#53868b', 'Biru Laut Gelap'),
        ('#8470ff', 'Biru Slate Cerah'),
        ('#7b68ee', 'Biru Medium Slate'),
        ('#6a5acd', 'Biru Slate'),
        ('#2a52be', 'Biru Indigo'),
    ],
        default='#00205b'
    )
    def __str__(self):
        return self.nama

class Kegiatan(models.Model):
    tahun_akademik = models.ForeignKey(TahunAkademik, on_delete=models.CASCADE)
    semester = models.CharField(choices=[('Ganjil','Ganjil'),('Genap','Genap')], max_length=20, default='Ganjil')
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
    metode = models.CharField(choices=[('email','Email'),('whatsapp','Whatsapp')], max_length=20, default='email')
    status = models.CharField(choices=[('Pending','Pending'),('Terkirim','Terkirim'),('Gagal','Gagal')], max_length=20, default='Pending')
    one_day_before = models.BooleanField(default=False)
    one_hour_before = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notifikasi untuk {self.user_fk}"
