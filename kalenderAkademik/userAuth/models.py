from django.db import models
from django.contrib.auth.models import AbstractUser
# Create your models here

class CustomUser(AbstractUser):
    peran = models.CharField(max_length=20, choices=[('admin', 'Admin'), ('dosen', 'Dosen'), ('mahasiswa', 'Mahasiswa')], default='mahasiswa')
    no_telpon = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(unique=True)

    def __str__(self):
        return f"{self.username}"