import os
import django
import sys

# 1. Mengatur Path agar Python bisa menemukan folder project
base_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(base_dir)

# 2. Mengarahkan ke settings di dalam folder 'core_alp'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core_alp.settings')

try:
    django.setup()
    print("✅ Koneksi ke sistem Smart Study Club berhasil.")
except Exception as e:
    print(f"❌ Gagal masuk ke sistem: {e}")
    sys.exit(1)

# Import model setelah django.setup()
from django.contrib.auth.models import User
from profiles_app.models import Profile
from alp_app.models import QuizResult

def jalankan_sinkronisasi():
    print("\n--- Memulai Perapihan Data Kemampuan Siswa ---")
    users = User.objects.all()
    total_berhasil = 0

    for user in users:
        # Mencari hasil kuis paling baru
        hasil_terakhir = QuizResult.objects.filter(user=user).order_by('-date').first()
        
        if hasil_terakhir:
            # Pastikan profil ada, lalu update skornya
            profil, created = Profile.objects.get_or_create(user=user)
            profil.ability_score = hasil_terakhir.theta_result
            profil.save()
            
            print(f"   [OK] {user.username} -> Skor: {hasil_terakhir.theta_result}")
            total_berhasil += 1
        else:
            print(f"   [SKIP] {user.username} belum mengerjakan kuis.")

    print(f"\n--- Selesai! {total_berhasil} data berhasil disinkronkan ---\n")

if __name__ == "__main__":
    jalankan_sinkronisasi()