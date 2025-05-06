from django.urls import path, include
from .views import Custom_login
from django.contrib.auth.views import LoginView, LogoutView

app_name = 'userAuth'
urlpatterns = [
    # path('', include('django.contrib.auth.urls')),
    path('login/', Custom_login.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
]