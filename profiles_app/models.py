# profiles_app/models.py

from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.exceptions import ObjectDoesNotExist  # Memastikan impor tersedia

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

    # Menggunakan related_name='user_profile' agar sinkron dengan panggilan di views dan admin
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='user_profile') 
    
    kelas = models.CharField(
        max_length=20, 
        choices=KELAS_CHOICES, 
        blank=True, 
        null=True, 
        verbose_name="Kelas Akademik"
    )
    
    # === DATA LAINNYA ===
    foto = models.ImageField(upload_to='profile_pics', blank=True, null=True)
    nama_lengkap = models.CharField(max_length=100, blank=True)
    level = models.CharField(max_length=50, blank=True, default="Pelajar Aktif")
    bio = models.TextField(max_length=500, blank=True)
    
    # === PARAMETER UTAMA IRT (MODEL RASCH) ===
    ability_score = models.FloatField(
        default=0.0, 
        verbose_name="Skor Kemampuan (Theta)",
        help_text="Estimasi kemampuan siswa berdasarkan Model Rasch (IRT)"
    )
    
    # === DATA UNTUK DASHBOARD/STATISTIK ===
    total_waktu_belajar = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00, verbose_name="Total Waktu Belajar (Jam)"
    )
    nilai_rata_rata = models.DecimalField(
        max_digits=5, decimal_places=2, default=0.00, verbose_name="Nilai Rata-rata Kuis"
    )

    # Tambahkan field points di sini agar sinkron dengan properti hierarki
    points = models.IntegerField(default=0, verbose_name="Poin Belajar")

    perubahan_waktu_belajar = models.CharField(max_length=10, default="↑ 0%")
    pesan_waktu_belajar = models.CharField(max_length=50, default="dari Minggu Lalu")
    pesan_nilai_rata_rata = models.CharField(max_length=50, default="Performa stabil")

    def __str__(self):
        return f'Profil {self.user.username}'
    
    @property
    def get_hierarchy_name(self):
        # Konversi jam (Decimal) ke menit secara akurat
        total_min = int(float(self.total_waktu_belajar) * 60)
        
        # Sekarang langsung mengambil dari self.points karena field sudah ada
        if total_min > 300:
            return "Pelajar Setia"
        elif total_min >= 60 and self.points >= 80:
            return "Pelajar Teladan"
        elif total_min >= 60:
            return "Pelajar Aktif"
        elif total_min >= 1:
            return "Pelajar Pemula"
        else:
            return "Pelajar Baru"
    
# --- SIGNALS (Sangat Penting agar User baru otomatis punya Profil) ---

@receiver(post_save, sender=User)
def create_or_save_user_profile(sender, instance, created, **kwargs):
    """
    Menangani pembuatan profil baru untuk user baru (created) 
    atau memperbarui profil yang sudah ada untuk user lama.
    """
    if created:
        # Gunakan get_or_create untuk memastikan profil dibuat hanya jika belum ada
        Profile.objects.get_or_create(user=instance)
    else:
        # Untuk user yang sudah ada, pastikan profil tersimpan saat user diupdate
        try:
            if hasattr(instance, 'user_profile'):
                instance.user_profile.save()
            else:
                # Menangani kasus user lama yang mungkin belum punya profil
                Profile.objects.get_or_create(user=instance)
        except (ObjectDoesNotExist, AttributeError):
            pass