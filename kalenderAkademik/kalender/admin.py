from django.contrib import admin
from .models import Notifikasi, Kategori, Kegiatan, TahunAkademik
# Register your models here.

@admin.register(Kategori)
class KategoriAdmin(admin.ModelAdmin):
    list_display = ('id', 'nama', 'warna')
    search_fields = ('nama',)
    list_filter = ('nama', 'warna', )
    ordering = ('id',)
    
@admin.register(Kegiatan)
class KegiatanAdmin(admin.ModelAdmin):
    list_display = ('id','tahun_akademik', 'semester', 'kategori_fk', 'nama', 'tgl_mulai', 'tgl_selesai', 'deskripsi')
    search_fields = ('nama',)
    list_filter = ('tahun_akademik', 'kategori_fk',)
    ordering = ('id',)
    readonly_fields = ('user_fk',)
    
    def save_model(self, request, obj, form, change):
        """
        Override user_fk.
        """
        if not change:
            obj.user_fk = request.user
        super().save_model(request, obj, form, change)
    
@admin.register(TahunAkademik)
class TahunAkademikAdmin(admin.ModelAdmin):
    list_display = ('id', 'tahun_akademik')
    search_fields = ('tahun_akademik',)
    list_filter = ('tahun_akademik',)
    ordering = ('id',)

@admin.register(Notifikasi)
class NotifikasiAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_fk', 'kegiatan_fk', 'metode', 'status', 'one_day_before', 'one_hour_before')
    search_fields = ('user_fk',)
    list_filter = ('kegiatan_fk', 'metode')
    ordering = ('id',)

# admin.site.register(TahunAkademik)
# admin.site.register(Kategori)
# admin.site.register(Kegiatan)
# admin.site.register(Notifikasi)