# profiles_app/views.py (FILE BARU)

from django.shortcuts import render, redirect
from django.contrib import messages
from allauth.account.decorators import login_required
from django.db import transaction

from .forms import UserForm, ProfileForm
from .models import Profile 

# Tambahkan import ini di bagian paling atas views.py (jika belum ada)
from django.contrib.auth import views as auth_views
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy

@login_required
@transaction.atomic 
def profile_settings(request):
    user = request.user
    profile = user.user_profile

    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=user)
        # Ambil data post apa adanya
        profile_form = ProfileForm(request.POST, request.FILES, instance=profile)

        # KHUSUS ADMIN: Kita hapus field 'kelas' dari pengecekan error 
        # karena kita tahu field ini di-disable di HTML
        if user.is_staff:
            if 'kelas' in profile_form.errors:
                del profile_form.errors['kelas']

        if user_form.is_valid() and profile_form.is_valid():
            # Simpan dulu tanpa commit untuk memanipulasi data
            p_form = profile_form.save(commit=False)
            if user.is_staff:
                p_form.kelas = "ADMIN" # Pastikan value ini sesuai dengan pilihan di models.py
            
            user_form.save()
            p_form.save() # Simpan ke database
            
            messages.success(request, 'Profil Anda berhasil diperbarui!')
            return redirect('profile_settings') 
        else:
            # Ini untuk melihat error detail di terminal jika masih gagal
            print(profile_form.errors)
            messages.error(request, 'Terjadi kesalahan saat menyimpan profil.')

    else:
        user_form = UserForm(instance=user)
        profile_form = ProfileForm(instance=profile)

    return render(request, 'profile_settings.html', {
        'user_form': user_form,
        'profile_form': profile_form,
        'profile': profile,
    })

# TAMBAHKAN CLASS INI DI DALAM VIEWS.PY
class MyPasswordChangeView(SuccessMessageMixin, auth_views.PasswordChangeView):
    # Nama file HTML industrial yang kamu kirim tadi
    template_name = 'password_change_form.html' 
    
    # Setelah sukses, balik ke halaman profil
    success_url = reverse_lazy('profile_settings')
    
    # Pesan yang bakal muncul di box hijau
    success_message = "Kunci enkripsi berhasil diperbarui! Password Anda telah diubah."