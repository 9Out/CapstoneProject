from django.shortcuts import render

app_name = 'home'
# Create your views here.
def home(request):
    return render(request, 'home/index.html')