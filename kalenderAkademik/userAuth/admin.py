from django.contrib import admin
from .models import CustomUser
from django.contrib.auth.admin import UserAdmin

# Register your models here.

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ['username', 'email', 'peran', 'no_telpon', 'is_staff']
    list_filter = ['is_staff', 'is_superuser', 'peran']
    search_fields = ['username', 'email']
    ordering = ('username',)
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('peran', 'no_telpon')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('email', 'peran', 'no_telpon')}),
    )

admin.site.register(CustomUser, CustomUserAdmin)
