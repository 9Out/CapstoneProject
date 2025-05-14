from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth import get_user_model
import re
from .models import CustomUser
from django.contrib.auth.models import Group

class CustomUserAddForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ('username', 'first_name', 'last_name', 'email', 'peran', 'no_telpon')
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Isi choices untuk peran berdasarkan grup yang ada
        self.fields['peran'].choices = [(group.name, group.name) for group in Group.objects.all()]
        
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError("Email ini sudah digunakan. Silakan gunakan email lain.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user

class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        label="Username atau Email",
        max_length=254,
        widget=forms.TextInput(attrs={
            'autofocus': True,
            'class': "input-field",
            'placeholder': "Username atau Email",
        }),
    )
    password = forms.CharField(
        label="Kata Sandi",
        widget=forms.PasswordInput(attrs={
            'class': "input-field",
            'placeholder': "Kata Sandi",
        })
    )

    def clean(self):
        input_value = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if input_value and password:
            UserModel = get_user_model()
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if re.match(email_pattern, input_value):
                try:
                    user = UserModel.objects.get(email=input_value)
                    self.cleaned_data['username'] = user.username
                except UserModel.DoesNotExist:
                    raise forms.ValidationError(
                        "Email tidak ditemukan. Silakan coba lagi."
                    )

        return super().clean()