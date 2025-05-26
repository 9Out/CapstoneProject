from django.contrib import admin
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.contrib.auth import get_user_model
from .models import Ormawa
from django import forms

class OrmawaForm(forms.ModelForm):
    class Meta:
        model = Ormawa
        fields = '__all__'
        
    user = forms.ModelMultipleChoiceField(
        queryset=get_user_model().objects.all(),
        widget=FilteredSelectMultiple(
            verbose_name='Users',
            is_stacked=False
        ),
        required=False
    )

        

@admin.register(Ormawa)
class OrmawaAdmin(admin.ModelAdmin):
    form = OrmawaForm
    list_display = ('nama', 'created_at', 'updated_at')
    search_fields = ('nama',)
    ordering = ('-created_at',)
    


# Register your models here.
