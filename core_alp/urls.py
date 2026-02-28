# core_alp/urls.py (Harus Diperiksa di Proyek Utama Anda)

from django.contrib import admin
from django.urls import path, include
# Impor yang diperlukan untuk media files:
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),

    path('', include('alp_app.urls')),
    path('profile/', include('profiles_app.urls')),
    path('dashboard/', include('dashboard_app.urls')), # <-- APP DASHBOARD
    path('manager/', include('manager_app.urls')),

]

# --- KONFIGURASI UNTUK MELAYANI FILE MEDIA SAAT DEBUG=TRUE ---
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)