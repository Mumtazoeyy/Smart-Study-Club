# core_alp/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),

    path('', include('alp_app.urls')),
    path('profile/', include('profiles_app.urls')),
    path('dashboard/', include('dashboard_app.urls')),
    path('manager/', include('manager_app.urls')),
]

# --- KONFIGURASI TAMBAHAN SAAT DEBUG = TRUE ---
if settings.DEBUG:
    # 1. Tambahkan Rute untuk Django Debug Toolbar
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns

    # 2. Melayani file MEDIA (foto profil, dll)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    
    # 3. Melayani file STATIC (CSS, JS, Icons)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)