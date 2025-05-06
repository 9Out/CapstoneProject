from django.shortcuts import render

# Create your views here.
def kalender(request):
    return render(request, 'kalender/kaldik.html')