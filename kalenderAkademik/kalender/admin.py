from django.contrib import admin
from .models import Notifikasi, Kategori, Kegiatan
# Register your models here.

admin.site.register(Kategori)
admin.site.register(Kegiatan)
admin.site.register(Notifikasi)