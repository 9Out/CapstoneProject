"""
URL configuration for kalenderAkademik project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from kalender.views import KegiatanListView, save_notification, category_list, add_kegiatan, delete_kegiatan, update_kegiatan

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('home.urls')),
    path('kalender/', include('kalender.urls')),
    path('about/', include('aboutUs.urls')),
    path('auth/', include('userAuth.urls')),
    path('api/events/', KegiatanListView.as_view(), name='kegiatan-list'),
    path('api/save-notification/', save_notification, name='save-notification'),
    path('api/categories/', category_list, name='category-list'),
    path('api/events/add/', add_kegiatan, name='add-kegiatan'),
    path('api/events/update/<int:id>/', update_kegiatan, name='update-kegiatan'),
    path('api/events/delete/<int:id>/', delete_kegiatan, name='delete-kegiatan'),
]

