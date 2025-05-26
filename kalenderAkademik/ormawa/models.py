from django.db import models
from django.conf import settings
# Create your models here.
class Ormawa(models.Model):
    nama = models.CharField(max_length=100, unique=True)
    deskripsi = models.TextField(blank=True, null=True)
    user = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name='ormawa_users',
        )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.nama

    

