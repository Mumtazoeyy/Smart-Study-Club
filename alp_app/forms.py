# alp_app/forms.py
from allauth.account.forms import SignupForm
from django import forms
from profiles_app.models import Profile
from .models import Course, Enrollment

class ExtendedSignupForm(SignupForm):
    kelas = forms.ChoiceField(
        choices=Profile.KELAS_CHOICES,
        required=True,
        label="Kelas Akademik"
    )

    def signup(self, request, user):
        # Allauth sudah membuat 'user', kita tinggal mengisi profilnya
        pilihan_kelas = self.cleaned_data.get('kelas')
        
        # Simpan ke Profile
        profil, created = Profile.objects.get_or_create(user=user)
        profil.kelas = pilihan_kelas
        profil.save()

        # Auto-Enrollment
        if pilihan_kelas:
            kategori_target = "SMP" if "smp" in pilihan_kelas.lower() else "SMA"
            courses = Course.objects.filter(category__name__icontains=kategori_target)
            for course in courses:
                Enrollment.objects.get_or_create(user=user, course=course)