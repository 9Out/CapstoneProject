from django.db import models
from django.contrib.auth.models import AbstractUser, Group
# Create your models here

class CustomUser(AbstractUser):
    peran = models.ForeignKey(Group, on_delete=models.SET_NULL, blank=True, null=True)
    no_telpon = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(unique=True, blank=False)

    def __str__(self):
        return f"{self.username}"

    @property
    def _peran_choices(self):
        return [(group.name, group.name) for group in Group.objects.all()]