from django.db import models
from django.conf import settings
# Create your models here.
class Ormawa(models.Model):
    nama = models.CharField(max_length=100, unique=True)
    deskripsi = models.TextField(blank=True, null=True)
    ketua = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='ketua_ormawa'
    )
    sekretaris = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='sekretaris_ormawa'
    )
    user = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name='ormawa_users',
        )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        super(Ormawa, self).save(*args, **kwargs)
        if self.ketua and self.ketua not in self.user.all():
            self.user.add(self.ketua)
        if self.sekretaris and self.sekretaris not in self.user.all():
            self.user.add(self.sekretaris)
        super(Ormawa, self).save(*args, **kwargs)
    
    def __str__(self):
        return self.nama

    

