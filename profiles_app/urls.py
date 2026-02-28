from django.urls import path, reverse_lazy
from . import views
from django.contrib.auth import views as auth_views
from django.contrib.messages.views import SuccessMessageMixin # 1. Import ini

# 2. Buat class bantuan agar pesan sukses bisa terkirim
class MyPasswordChangeView(SuccessMessageMixin, auth_views.PasswordChangeView):
    template_name = 'password_change_form.html'
    success_url = reverse_lazy('profile_settings')
    success_message = "ACCESS GRANTED: Kunci enkripsi berhasil diperbarui!" # Pesan yang akan muncul

urlpatterns = [
    path('', views.profile_settings, name='profile_settings'), 

    # 3. Panggil class yang baru kita buat tadi
    path('password-change/', MyPasswordChangeView.as_view(), name='password_change'),
]