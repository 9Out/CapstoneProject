from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import get_user_model
import re

class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        label="Username atau Email",
        max_length=254,
        widget=forms.TextInput(attrs={'autofocus': True}),
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