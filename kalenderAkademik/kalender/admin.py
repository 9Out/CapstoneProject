from django.contrib import admin
from .models import Notifikasi, Kategori, Kegiatan, TahunAkademik
# Register your models here.

admin.site.register(TahunAkademik)
admin.site.register(Kategori)
admin.site.register(Kegiatan)
admin.site.register(Notifikasi)