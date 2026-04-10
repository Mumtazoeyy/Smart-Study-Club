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

if settings.DEBUG:
    # 1. Rute untuk Django Debug Toolbar (Hanya saat Debug)
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
    
    # 2. Melayani file STATIC & MEDIA (Cara standar saat Debug)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

else:
    # 3. PENTING: Agar gambar tetap muncul di PythonAnywhere saat DEBUG = False
    urlpatterns += [
        path('media/<path:path>', serve, {'document_root': settings.MEDIA_ROOT}),
        path('static/<path:path>', serve, {'document_root': settings.STATIC_ROOT}),
    ]