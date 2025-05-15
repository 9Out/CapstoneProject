from django.conf import settings
from django.db import models

# Create your models here.
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
        ('#fafad2', 'Aprikot Muda (Light Goldenrod Yellow)'),
        ('#ffebcd', 'Almond Pucat (Blanched Almond)'),
        ('#e6e6fa', 'Lavender'),
        ('#fff0f5', 'Lavender Kemerahan (Lavender Blush)'),
        ('#4876ff', 'Biru Cerah'),
        ('#5f9ea0', 'Biru Cadet'),
        ('#1e90ff', 'Biru Dodger'),
        ('#2a52be', 'Biru Indigo'),
        ('#add8e6', 'Biru Langit Muda (Light Blue)'),
        ('#87ceeb', 'Biru Langit Cerah'),
        ('#00bfff', 'Biru Langit Dalam'),
        ('#b0e0e6', 'Biru Langit Pucat (Powder Blue)'),
        ('#7ec0ee', 'Biru Langit Sedang'),
        ('#00b7eb', 'Biru Langit'),
        ('#53868b', 'Biru Laut Gelap'),
        ('#000080', 'Biru Laut Tua (Navy)'),
        ('#0000cd', 'Biru Medium (Medium Blue)'),
        ('#7b68ee', 'Biru Medium Slate'),
        ('#191970', 'Biru Tengah Malam'),
        ('#6ca6cd', 'Biru Periwinkle'),
        ('#4169e1', 'Biru Royal'),
        ('#6a5acd', 'Biru Slate'),
        ('#8470ff', 'Biru Slate Cerah'),
        ('#4682b4', 'Biru Baja'),
        ('#00205b', 'Biru Tua'),
        ('#00008b', 'Biru Tua Gelap (Dark Blue)'),
        ('#008b8b', 'Biru Kehijauan Gelap (Dark Cyan)'),
        ('#f5fffa', 'Biru Mint Krim (Mint Cream)'),
        ('#40e0d0', 'Biru Pirus (Turquoise)'),
        ('#483d8b', 'Biru Slate Gelap (Dark Slate Blue)'),
        ('#8a2be2', 'Biru Violet (Blue Violet)'),
        ('#deb887', 'Cokelat Burly'),
        ('#d2691e', 'Cokelat Cokelat'),
        ('#8b4513', 'Cokelat Kayu Manis (Saddle Brown)'),
        ('#a52a2a', 'Cokelat Merah Bata (Brown)'),
        ('#cd853f', 'Cokelat Peru'),
        ('#f4a460', 'Cokelat Sandy'),
        ('#a0522d', 'Cokelat Sienna'),
        ('#d2b48c', 'Cokelat Tan'),
        ('#bc8f8f', 'Cokelat Rosy'),
        ('#8b5a2b', 'Cokelat Tua (Dark Goldenrod)'),
        ('#800000', 'Cokelat Tua Pekat (Maroon)'),
        ('#fffff0', 'Gading (Ivory)'),
        ('#ffd700', 'Emas'),
        ('#daa520', 'Emas Batangan (Goldenrod)'),
        ('#eee8aa', 'Emas Pucat (Pale Goldenrod)'),
        ('#b8860b', 'Emas Tua (Dark Goldenrod)'),
        ('#00ff00', 'Hijau Terang'),
        ('#00c853', 'Hijau'),
        ('#adff2f', 'Hijau Kekuningan'),
        ('#7fff00', 'Hijau Chartreuse'),
        ('#b3ee3a', 'Hijau Cerah'),
        ('#76ee00', 'Hijau Cerah'), 
        ('#228b22', 'Hijau Hutan'),
        ('#32cd32', 'Hijau Lime'),
        ('#00fa9a', 'Hijau Medium'),
        ('#b4eeb4', 'Hijau Mint'),
        ('#00ff7f', 'Hijau Musim Semi'),
        ('#98fb98', 'Hijau Pucat'),
        ('#9aff9a', 'Hijau Pucat Cerah'),
        ('#20b2aa', 'Hijau Laut'),
        ('#66cdaa', 'Hijau Laut Medium'),
        ('#3cb371', 'Hijau Laut Sedang'),
        ('#2e8b57', 'Hijau Laut Tua (Sea Green)'),
        ('#8fbc8f', 'Hijau Laut Pucat (Dark Sea Green)'),
        ('#66cd00', 'Hijau Sedang'),
        ('#006400', 'Hijau Tua (Dark Green)'),
        ('#556b2f', 'Hijau Zaitun Coklat (Dark Olive Green)'),
        ('#9acd32', 'Hijau Zaitun'),
        ('#6b8e23', 'Hijau Zaitun Gelap'),
        ('#000000', 'Hitam'),
        ('#ffebc5', 'Jagung Sutra (Cornsilk)'),
        ('#fff8dc', 'Jagung Sutra Pucat (Cornsilk)'), 
        ('#ff7f50', 'Koral'),
        ('#f08080', 'Koral Cerah'),
        ('#ff7256', 'Koral Cerah'), 
        ('#e9967a', 'Koral Terang'),
        ('#fffaf0', 'Krem Bunga (Floral White)'),
        ('#f0fff0', 'Krem Embun Madu (Honeydew)'),
        ('#fdf5e6', 'Krem Linen (Old Lace)'),
        ('#faf0e6', 'Krem Navajo (Linen)'),
        ('#ffffe0', 'Kuning Cerah (Light Yellow)'),
        ('#cdad00', 'Kuning Emas'),
        ('#ffff00', 'Kuning Lemon (Yellow)'), 
        ('#e3cf57', 'Kuning Mustard'),
        ('#fffacd', 'Kuning Navajo (Lemon Chiffon)'),
        ('#f0e68c', 'Kuning Pucat'),
        ('#adff2f', 'Kuning-Hijau (Green Yellow)'), 
        ('#ffcc00', 'Kuning'), # 
        ('#ff00ff', 'Magenta'),
        ('#ffefd5', 'Moccasin'),
        ('#ffe4b5', 'Moka Pucat (Moccasin)'), 
        ('#ffe4e1', 'Mawar Kabut (Misty Rose)'),
        ('#ffdead', 'Navajo Putih'),
        ('#ff8247', 'Oranye Koral'),
        ('#ff4500', 'Oranye Merah Jingga (Orange Red)'), 
        ('#ffa500', 'Oranye'),
        ('#ff8c00', 'Oranye Tua'),
        ('#ffdab9', 'Peach Puff'),
        ('#c0c0c0', 'Perak'),
        ('#d8bfd8', 'Thistle'),
        ('#00e5ee', 'Turkis Cerah'),
        ('#7fffd4', 'Turkis Cerah'),
        ('#00ced1', 'Turkis Gelap'),
        ('#48d1cc', 'Turkis Medium'),
        ('#afeeee', 'Turkis Pucat'),
        ('#ee82ee', 'Ungu Violet'),
        ('#da70d6', 'Ungu Orchid'),
        ('#dda0dd', 'Ungu Plum'),
        ('#9932cc', 'Ungu Gelap'),
        ('#ba55d3', 'Ungu Medium'),
        ('#b452cd', 'Ungu Cerah'),
        ('#cd69c9', 'Ungu Cerah'), 
        ('#8b008b', 'Ungu Magenta'),
        ('#9400d3', 'Ungu Violet Gelap'),
        ('#4b0082', 'Ungu Tua'),
        ('#800080', 'Ungu Tua Pekat (Purple)'),
        ('#663399', 'Ungu Rebecca'),
        ('#e0ffff', 'Sian Muda (Light Cyan)'),
        ('#00ffff', 'Sian (Cyan/Aqua)'),
        ('#008080', 'Teal'),
        ('#d3d3d3', 'Abu-abu Sangat Muda (Light Gray)'),
        ('#f8f8ff', 'Putih Hantu (Ghost White)'),
        ('#f0f8ff', 'Putih Alice (Alice Blue)'),
        ('#faebd7', 'Putih Antik (Antique White)'),
        ('#ffefdb', 'Putih Antik Pucat (Papaya Whip)'), 
        ('#f5f5f5', 'Putih Asap (White Smoke)'),
        ('#fff5ee', 'Putih Kerang (Seashell)'),
        ('#ffffff', 'Putih'),
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
    warna = models.CharField(unique=True,
        max_length=7,  
        choices = COLOR_CHOICES,
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
    # updated_at = models.DateTimeField(auto_now=True)

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
