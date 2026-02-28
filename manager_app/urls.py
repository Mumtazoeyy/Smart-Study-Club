from django.urls import path
from . import views

urlpatterns = [
    # Dashboard Utama
    path('', views.admin_dashboard, name='manager_dashboard'),
    path('management/import-materi/', views.import_materi_view, name='import_materi'),
]