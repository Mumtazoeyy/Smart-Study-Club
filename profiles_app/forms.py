# profiles_app/forms.py (FILE BARU)

from django import forms
from django.contrib.auth.models import User
from .models import Profile

# Formulir 1: Mengedit data dasar User (Email)
class UserForm(forms.ModelForm):
    # Field email diizinkan untuk di-edit dan wajib diisi
    email = forms.EmailField(required=True, 
                             widget=forms.EmailInput(attrs={'class': 'form-input w-full px-3 py-2 border rounded-lg', 'placeholder': 'Email Anda'})) 

    class Meta:
        model = User
        fields = ('email',)

# Formulir 2: Mengedit data Profile tambahan
class ProfileForm(forms.ModelForm):
    # SESUAIKAN: Mengambil pilihan kelas langsung dari models.py
    kelas = forms.ChoiceField(
        choices=Profile.KELAS_CHOICES, 
        required=False,
        widget=forms.Select(attrs={'class': 'form-input w-full px-3 py-2 border rounded-lg'})
    )
    
    # Menambahkan widget styling dasar
    nama_lengkap = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-input w-full px-3 py-2 border rounded-lg'}))
    level = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-input w-full px-3 py-2 border rounded-lg', 'readonly': 'readonly'}))
    bio = forms.CharField(required=False, widget=forms.Textarea(attrs={'class': 'form-textarea w-full px-3 py-2 border rounded-lg', 'rows': 3}))
    foto = forms.ImageField(required=False, widget=forms.FileInput(attrs={'class': 'form-input w-full px-3 py-2 border rounded-lg'}))
    
    class Meta:
        model = Profile
        # SESUAIKAN: Tambahkan 'kelas' ke dalam fields agar bisa disimpan
        fields = ('foto', 'nama_lengkap', 'kelas', 'level', 'bio')