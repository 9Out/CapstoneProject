from django.shortcuts import render

# Create your views here.
def kaldik(request):
    return render(request, 'kalender/kaldik.html')