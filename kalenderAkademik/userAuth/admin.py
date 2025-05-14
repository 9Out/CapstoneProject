from django.contrib import admin
from .models import CustomUser
from django.contrib.auth.admin import UserAdmin
from .forms import CustomUserAddForm
from django import forms
from django.db import models

# Register your models here.

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ['username', 'email', 'peran', 'no_telpon', 'is_staff']
    list_filter = ['is_staff', 'is_superuser', 'peran']
    search_fields = ['username', 'email']
    ordering = ('username',)
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email', 'peran', 'no_telpon')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'first_name', 'last_name', 'email', 'peran', 'no_telpon', 'password1', 'password2'),
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser'),
        }),
    )
    
    add_form = CustomUserAddForm
    formfield_overrides = {
        models.ForeignKey: {'widget': forms.Select},
    }

admin.site.register(CustomUser, CustomUserAdmin)