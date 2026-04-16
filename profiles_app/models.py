# profiles_app/models.py

from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Avg # Tambahkan import ini

class Profile(models.Model):
    # DAFTAR PILIHAN KELAS
    KELAS_CHOICES = [
        ('smp1', 'Kelas 7 (SMP 1)'),
        ('smp2', 'Kelas 8 (SMP 2)'),
        ('smp3', 'Kelas 9 (SMP 3)'),
        ('sma1', 'Kelas 10 (SMA 1)'),
        ('sma2', 'Kelas 11 (SMA 2)'),
        ('sma3', 'Kelas 12 (SMA 3)'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='user_profile') 
    
    kelas = models.CharField(
        max_length=20, 
        choices=KELAS_CHOICES, 
        blank=True, 
        null=True, 
        verbose_name="Kelas Akademik"
    )
    
    foto = models.ImageField(upload_to='profile_pics', blank=True, null=True)
    nama_lengkap = models.CharField(max_length=100, blank=True)
    level = models.CharField(max_length=50, blank=True, default="Pelajar Aktif")
    bio = models.TextField(max_length=500, blank=True)
    
    # Field statis tetap ada agar tidak merusak database (Migration tetap aman)
    ability_score = models.FloatField(
        default=0.0, 
        verbose_name="Skor Kemampuan (Theta)",
        help_text="Estimasi kemampuan siswa berdasarkan Model Rasch (IRT)"
    )
    
    total_waktu_belajar = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00, verbose_name="Total Waktu Belajar (Jam)"
    )
    nilai_rata_rata = models.DecimalField(
        max_digits=5, decimal_places=2, default=0.00, verbose_name="Nilai Rata-rata Kuis"
    )

    points = models.IntegerField(default=0, verbose_name="Poin Belajar")
    perubahan_waktu_belajar = models.CharField(max_length=10, default="↑ 0%")
    pesan_waktu_belajar = models.CharField(max_length=50, default="dari Minggu Lalu")
    pesan_nilai_rata_rata = models.CharField(max_length=50, default="Performa stabil")

    def __str__(self):
        return f'Profil {self.user.username}'

    # === LOGIKA OTOMATIS: MENGHITUNG DARI AKTIVITAS NYATA ===

    # === LOGIKA OTOMATIS: MENGHITUNG DARI AKTIVITAS NYATA ===

    @property
    def get_calculated_theta(self):
        from alp_app.models import QuizResult
        latest = QuizResult.objects.filter(user=self.user).order_by('-date').first()
        # Pembulatan ke 2 angka di belakang koma (misal: 0.41)
        return round(latest.theta_result, 2) if latest else 0.0

    @property
    def get_calculated_avg(self):
        from django.db import models
        from alp_app.models import QuizResult
        avg = QuizResult.objects.filter(user=self.user).aggregate(models.Avg('score'))['score__avg']
        # Pembulatan ke 2 angka di belakang koma (misal: 85.50)
        return round(float(avg), 2) if avg else 0.00

    @property
    def get_calculated_time(self):
        from alp_app.models import StudySession
        from django.db.models import Sum
        
        # Karena di database kamu tidak ada end_time, tapi ada field 'duration'
        # Kita langsung jumlahkan saja field duration tersebut.
        total_duration = StudySession.objects.filter(
            user=self.user
        ).aggregate(
            total=Sum('duration')
        )['total']
        
        # Jika total_duration sudah dalam satuan menit, langsung return.
        # Jika dalam detik, bagi 60. (Asumsi: duration kamu dalam menit/angka)
        if total_duration:
            return round(float(total_duration), 2)
        
        return 0.00

    @property
    def get_hierarchy_name(self):
        total_min = self.get_calculated_time
        # 1. Pelajar Setia (Lebih dari 5 Jam / 300 Menit)
        if total_min >= 300:
            return "Pelajar Setia"
        # 2. Pelajar Teladan (Minimal 1 Jam DAN Poin Tinggi >= 80)
        elif total_min >= 60 and self.points >= 80:
            return "Pelajar Teladan"
        # 3. Pelajar Aktif (Minimal 1 Jam / 60 Menit)
        elif total_min >= 60:
            return "Pelajar Aktif"
        # 4. Pelajar Pemula (Minimal 1 Menit)
        elif total_min >= 1:
            return "Pelajar Pemula"
        # 5. Pelajar Baru (0 Menit atau Baru Daftar)
        else:
            return "Pelajar Baru"
    
# --- SIGNALS ---

@receiver(post_save, sender=User)
def create_or_save_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.get_or_create(user=instance)
    else:
        try:
            if hasattr(instance, 'user_profile'):
                instance.user_profile.save()
            else:
                Profile.objects.get_or_create(user=instance)
        except (ObjectDoesNotExist, AttributeError):
            pass