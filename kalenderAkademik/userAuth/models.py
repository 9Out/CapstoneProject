from django.db import models
from django.contrib.auth.models import AbstractUser, Group

class CustomUser(AbstractUser):
    peran = models.ForeignKey(Group, on_delete=models.SET_NULL, blank=True, null=True, related_name='users_with_this_role')
    no_telpon = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(unique=True, blank=False)
    _original_peran = None

#    Inisialisasi CustomUser, menyimpan nilai awal 'peran' untuk melacak perubahan pada save.
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._original_peran = self.peran_id

    # Menyimpan instance CustomUser, menyinkronkan 'peran' dengan grup yang sesuai.
    # Menghapus dari grup lama dan menambahkan ke grup baru jika 'peran' berubah.
    def save(self, *args, **kwargs):
        is_new = self._state.adding
        super().save(*args, **kwargs)
        if self.peran_id != self._original_peran or (is_new and self.peran_id is not None):
            if self._original_peran is not None and self._original_peran != self.peran_id:
                try:
                    old_group = Group.objects.get(pk=self._original_peran)
                    self.groups.remove(old_group)
                except Group.DoesNotExist:
                    pass
            if self.peran_id is not None:
                try:
                    new_group = Group.objects.get(pk=self.peran_id)
                    self.groups.add(new_group)
                except Group.DoesNotExist:
                    pass
            elif self.peran_id is None and self._original_peran is not None:
                try:
                    old_group = Group.objects.get(pk=self._original_peran)
                    self.groups.remove(old_group)
                except Group.DoesNotExist:
                    pass
            self._original_peran = self.peran_id

    def __str__(self):
        return f"{self.username}"

    # Mengembalikan daftar pilihan peran (grup) yang tersedia.
    @property
    def _peran_choices(self):
        return [(group.name, group.name) for group in Group.objects.all()]