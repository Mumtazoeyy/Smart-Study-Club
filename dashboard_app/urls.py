# dashboard_app/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # Nama URL tetap 'dashboard' agar tidak ada perubahan di base.html
    path('', views.dashboard_view, name='dashboard'),

    path('history/delete/<int:pk>/', views.delete_history_item, name='delete_history_item'),
    path('history/clear/', views.clear_all_history, name='clear_all_history'),

    path('history/all/', views.history_full_view, name='history_full_view'),

    path('leaderboard/', views.leaderboard_view, name='leaderboard'),
]