from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve # Tambahkan ini untuk melayani media di prod
import re

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('', include('alp_app.urls')),
    path('profile/', include('profiles_app.urls')),
    path('dashboard/', include('dashboard_app.urls')),
    path('manager/', include('manager_app.urls')),
]

# --- KONFIGURASI TAMBAHAN ---

