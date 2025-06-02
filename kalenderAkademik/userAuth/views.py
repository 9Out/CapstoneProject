from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from .forms import CustomAuthenticationForm
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy


class Custom_login(LoginView):
    template_name = 'userAuth/login.html'
    form_class = CustomAuthenticationForm
    redirect_authenticated_user = True
    
    def get_success_url(self):
        user = self.request.user
        if user.is_authenticated:
            if user.is_staff: 
                return reverse_lazy('admin:index')
            else:
                return reverse_lazy('home:home') 
        return super().get_success_url()
    


# def login_view(request):
#     if request.method == 'POST':
#         form = CustomAuthForm(request, data=request.POST)
#         if form.is_valid():
#             user = form.get_user()
#             if user.check_password(form.cleaned_data['password']):
#                 login(request, user)
#                 return redirect('home')  # Redirect setelah login berhasil
#             else:
#                 form.add_error(None, "Password is incorrect")
#     else:
#         form = CustomAuthForm()
#
#     return render(request, 'userAuth/log.html', {'form': form})
